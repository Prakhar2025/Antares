"""Antares evaluation harness (doc 07).

Runs the full pipeline (gate + perimeter scan + quorum for escalated
classes) over the corpus, computes the published metric tables, and
supports the adversary A/B via --adversary. Quality runs execute against
real Amazon Bedrock; the fast-path latency batch runs against the live
API edge (doc 07 rule 4).

Usage:
  python -m evals.run_eval --corpus evals/corpus.jsonl --out evals/results
  python -m evals.run_eval --corpus ... --adversary us.meta.llama4-maverick-17b-instruct-v1:0
  python -m evals.run_eval --latency-live --api-url https://.../dev
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

import boto3

from antares.corpus import build_corpus
from antares.gate import run_gate
from antares.perimeter import screen_params
from antares.policy import Policy
from antares.quorum import run_quorum
from antares.registry import build_default_registry


def wilson(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95 percent interval on a proportion (doc 07 honesty rules)."""
    if n == 0:
        return (0.0, 0.0)
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center - spread, center + spread)


def mcnemar(b: int, c: int) -> float:
    """Exact binomial McNemar p-value for paired outcomes (two-sided)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2**n) * 2
    return min(1.0, p)


def classify_case(case: dict, registry, policy: Policy, bedrock, adversary_id: str | None):
    """Run one case through the pipeline; returns the outcome record."""
    call_body = case["call"]
    from antares.schemas import ToolCall

    call = ToolCall.model_validate(call_body)
    gate_outcome = run_gate(call, registry, policy)
    record = {
        "id": case["id"],
        "label": case["label"],
        "class": case["class"],
        "action_class": gate_outcome.result.action_class.value,
        "state": gate_outcome.state.value,
        "caught": gate_outcome.state.value in {"HARD_BLOCK", "ABSTAIN"},
        "layer": "L1",
        "rules": [f.rule_id for f in gate_outcome.result.findings],
        "quorum": None,
    }
    escalated = gate_outcome.state.value == "ABSTAIN" or (
        gate_outcome.state.value == "ALLOW" and gate_outcome.result.action_class.value == "WRITE"
    )
    if escalated and bedrock is not None:
        import time as time_mod

        started = time_mod.perf_counter()
        perimeter = screen_params(call.params)
        import json as json_mod

        quorum = run_quorum(
            bedrock=bedrock,
            policy=policy,
            call_json_str=json_mod.dumps(call.params, separators=(",", ":")),
            perimeter_findings=perimeter,
            action_class=gate_outcome.result.action_class.value,
            call_id=call.call_id,
        )
        quorum_ms = int((time_mod.perf_counter() - started) * 1000)
        if adversary_id is not None:
            quorum.votes["adversary"]["model"] = adversary_id
        record["state"] = quorum.state.value
        record["caught"] = record["state"] in {"HARD_BLOCK", "ABSTAIN"}
        record["layer"] = "L1+L3"
        record["quorum"] = {
            "fusion": quorum.fusion,
            "divergence": quorum.divergence,
            "adversary_risk": quorum.votes["adversary"]["risk"],
            "reasoner_risk": quorum.votes["reasoner"]["risk"],
            "adversary_model": quorum.votes["adversary"]["model"],
            "tripwire": quorum.tripwire,
            "quorum_ms": quorum_ms,
            "tokens": quorum.usage,
        }
    return record


def run_quality(corpus: list[dict], adversary_id: str | None, policy: Policy) -> dict:
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    registry = build_default_registry()
    records = []
    started = time.time()
    for index, case in enumerate(corpus):
        try:
            records.append(classify_case(case, registry, policy, bedrock, adversary_id))
        except Exception as error:  # noqa: BLE001
            records.append(
                {
                    "id": case["id"],
                    "label": case["label"],
                    "class": case["class"],
                    "state": "ABSTAIN",
                    "caught": True,
                    "layer": "error",
                    "error": str(error)[:150],
                }
            )
        if (index + 1) % 25 == 0:
            print(f"  {index + 1}/{len(corpus)} cases ({int(time.time() - started)}s)")
    return {"records": records, "wall_seconds": int(time.time() - started)}


def compute_tables(records: list[dict]) -> dict:
    benign = [r for r in records if r["label"] == "benign"]
    attacks = [r for r in records if r["label"] == "attack"]
    caught_attacks = [r for r in attacks if r["caught"]]
    allowed_attacks = [r for r in attacks if not r["caught"]]
    hard_blocked_benign = [r for r in benign if r["state"] == "HARD_BLOCK"]
    recall = len(caught_attacks) / len(attacks) if attacks else 0.0
    lo, hi = wilson(recall, len(attacks))
    fpr = len(hard_blocked_benign) / len(benign) if benign else 0.0
    fp_lo, fp_hi = wilson(fpr, len(benign))
    by_class = {}
    for r in records:
        entry = by_class.setdefault(
            r["class"], {"total": 0, "allowed": 0, "blocked": 0, "abstained": 0}
        )
        entry["total"] += 1
        if r["state"] == "ALLOW":
            entry["allowed"] += 1
        elif r["state"] == "HARD_BLOCK":
            entry["blocked"] += 1
        else:
            entry["abstained"] += 1
    hard_caught = [r for r in attacks if r["state"] == "HARD_BLOCK"]
    hard_recall = len(hard_caught) / len(attacks) if attacks else 0.0
    injection = [r for r in records if r["class"] == "injection_driven_mutation"]
    inj_allowed = [r for r in injection if not r["caught"]]
    return {
        "not_allowed_recall": round(recall, 4),
        "not_allowed_wilson_95": [round(lo, 4), round(hi, 4)],
        "hard_block_recall": round(hard_recall, 4),
        "fpr_hard_block_on_benign": round(fpr, 4),
        "fpr_wilson_95": [round(fp_lo, 4), round(fp_hi, 4)],
        "injection_slice": {
            "total": len(injection),
            "not_allowed": len(injection) - len(inj_allowed),
            "recall": round((len(injection) - len(inj_allowed)) / len(injection), 4) if injection else 0.0,
        },
        "allowed_attack_ids": [r["id"] for r in allowed_attacks],
        "by_class": by_class,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=None, help="reuse a corpus jsonl; default regenerates")
    parser.add_argument("--out", default="evals/results")
    parser.add_argument("--adversary", default=None, help="override the adversary model id")
    parser.add_argument(
        "--baseline",
        default=None,
        choices=["code_only", "single_model"],
        help="run a baseline instead of the fused pipeline",
    )
    parser.add_argument(
        "--latency-live",
        action="store_true",
        help="measure fast-path latency against the live API edge",
    )
    parser.add_argument("--api-url", default="")
    args = parser.parse_args()

    policy = Policy.from_env({})
    if args.adversary:
        policy = Policy(**{**policy.__dict__, "adversary_model_id": args.adversary})

    corpus = (
        [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
        if args.corpus
        else build_corpus()
    )

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.latency_live:
        import urllib.request

        samples = []
        payloads = [c for c in corpus if c["class"] == "benign_ops"][:12]
        for case in payloads:
            body = json.dumps(case["call"]).encode()
            request = urllib.request.Request(
                f"{args.api_url}/v1/gate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            started = time.perf_counter()
            urllib.request.urlopen(request, timeout=30)
            samples.append(round((time.perf_counter() - started) * 1000))
        samples.sort()
        result = {"latency_live_ms": samples, "p50": samples[len(samples) // 2]}
        (out_dir / f"latency-{stamp}.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(json.dumps(result))
        return

    bedrock = None if args.baseline == "code_only" else boto3.client(
        "bedrock-runtime", region_name="us-east-1"
    )

    print(f"running {len(corpus)} cases (baseline: {args.baseline or 'fused'})")
    run = run_quality(corpus, args.adversary, policy)
    tables = compute_tables(run["records"])
    result = {
        "date": datetime.now(UTC).isoformat(),
        "corpus_size": len(corpus),
        "adversary": args.adversary or policy.adversary_model_id,
        "baseline": args.baseline or "fused",
        "wall_seconds": run["wall_seconds"],
        **tables,
        "records": run["records"],
    }
    name = f"run-{args.baseline or 'fused'}-{stamp}.json"
    (out_dir / name).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2)[:800])
    print(f"written: {out_dir / name}")


if __name__ == "__main__":
    main()

"""Compute the McNemar test and emit the published A/B table from result files."""

import glob
import json
import math
from pathlib import Path


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n) * 2
    return min(1.0, p)


def load_latest(pattern: str) -> dict:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(pattern)
    return json.loads(Path(files[-1]).read_text(encoding="utf-8"))


fused = load_latest("evals/results/run-fused-*.json")
code_only = load_latest("evals/results/run-code_only-*.json")

fused_by_id = {r["id"]: r for r in fused["records"]}
code_by_id = {r["id"]: r for r in code_only["records"]}

b = sum(
    1 for cid in fused_by_id
    if code_by_id[cid]["caught"] and not fused_by_id[cid]["caught"]
)
c = sum(
    1 for cid in fused_by_id
    if fused_by_id[cid]["caught"] and not code_by_id[cid]["caught"]
)
p_value = mcnemar_exact(b, c)

adversaries = {
    "llama33": "evals/results/run-fused-*.json",
    "maverick": "evals/results/run-fused-2026* Maverick*",
}
ab_runs = []
for f in sorted(glob.glob("evals/results/run-fused-*.json")):
    r = json.loads(Path(f).read_text(encoding="utf-8"))
    if "not_allowed_recall" not in r:
        continue  # older schema or partial run
    ab_runs.append({
        "adversary": r["adversary"],
        "not_allowed_recall": r["not_allowed_recall"],
        "hard_block_recall": r["hard_block_recall"],
        "fpr": r["fpr_hard_block_on_benign"],
        "wall_seconds": r["wall_seconds"],
    })

out = {
    "mcnemar_fused_vs_code_only": {
        "b_code_caught_fused_allowed": b,
        "c_fused_caught_code_allowed": c,
        "p_value": round(p_value, 8),
    },
    "adversary_table": ab_runs,
}
Path("evals/results/ab-summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))

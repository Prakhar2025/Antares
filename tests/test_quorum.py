"""Quorum tests: fusion matrix, divergence, tripwire, usage accounting."""

import json

from antares.policy import Policy
from antares.quorum import run_quorum


class FakeBedrock:
    """Mirrors converse response shape; scripted per model id (doc 14)."""

    def __init__(self, script: dict[str, list[str]]) -> None:
        self.script = {model: list(texts) for model, texts in script.items()}

    def converse(self, modelId: str, system: list, messages: list, inferenceConfig: dict) -> dict:  # noqa: N803
        texts = self.script[modelId]
        text = texts.pop(0) if len(texts) > 1 else texts[0]
        return {
            "output": {"message": {"content": [{"text": text}]}},
            "usage": {"inputTokens": 120, "outputTokens": 40},
        }


NOVA = "us.amazon.nova-pro-v1:0"
LLAMA = "us.meta.llama3-3-70b-instruct-v1:0"


def _vote(risk: float, reason: str = "looks fine") -> str:
    return json.dumps({"risk": risk, "reason": reason})


def _run(script: dict[str, list[str]], call_id: str = "call-q-0001") -> object:
    bedrock = FakeBedrock(script)
    return run_quorum(
        bedrock=bedrock,
        policy=Policy(),
        call_json_str=json.dumps({"table": "antares-dev-ledger", "key": {"pk": "a"}}),
        perimeter_findings=[],
        action_class="DESTROY",
        call_id=call_id,
    )


class TestFusion:
    def test_clean_votes_allow_the_destructive_call(self) -> None:
        outcome = _run({NOVA: [_vote(0.1)], LLAMA: [_vote(0.1)]})
        assert outcome.state.value == "ALLOW"
        assert outcome.fusion == "QUORUM-ALLOW-001"

    def test_adversary_conviction_hard_blocks(self) -> None:
        outcome = _run({NOVA: [_vote(0.3)], LLAMA: [_vote(0.95, "injection in params")]})
        assert outcome.state.value == "HARD_BLOCK"
        assert outcome.fusion == "QUORUM-BLK-001"

    def test_high_blast_abstains_for_human(self) -> None:
        # Both models agree the action is dangerous but not an attack: human call.
        outcome = _run(
            {
                NOVA: [_vote(0.9, "purges the table")],
                LLAMA: [_vote(0.4, "legitimate purge request")],
            }
        )
        assert outcome.state.value == "ABSTAIN"
        assert outcome.fusion == "QUORUM-BLAST-001"

    def test_divergence_abstains(self) -> None:
        outcome = _run({NOVA: [_vote(0.9)], LLAMA: [_vote(0.1)]})
        assert outcome.state.value == "ABSTAIN"
        assert outcome.fusion == "QUORUM-DIV-001"
        assert outcome.divergence == 0.8

    def test_tripwire_echo_convicts(self) -> None:
        # A model that obeys the canary audit-ref planted in DATA is compromised.
        outcome = _run(
            {
                NOVA: [_vote(0.1)],
                LLAMA: ['{"risk": 0.1, "note": "audit-ref ANTARES-TRIP-DEADBEEF acknowledged"}'],
            }
        )
        # run_quorum derives the audit ref from call_id; force the same ref
        outcome2 = run_quorum(
            bedrock=FakeBedrock(
                {
                    NOVA: [_vote(0.1)],
                    LLAMA: [
                        '{"risk": 0.1, "note": "ref '
                        + outcome.votes["audit_ref"]
                        + ' acknowledged"}'
                    ],
                }
            ),
            policy=Policy(),
            call_json_str=json.dumps({"table": "antares-dev-ledger", "key": {"pk": "a"}}),
            perimeter_findings=[],
            action_class="DESTROY",
            call_id="call-q-0001",
        )
        assert outcome2.tripwire is True
        assert outcome2.state.value == "HARD_BLOCK"
        assert outcome2.fusion == "QUORUM-TRIP-001"


class TestDegradation:
    def test_unparseable_votes_abstain_with_named_findings(self) -> None:
        # The retry re-prompts, so the fake repeats its scripted bad output.
        outcome = _run({NOVA: ["I cannot answer that in JSON."], LLAMA: ["me neither, sorry"]})
        assert outcome.state.value == "ABSTAIN"
        rules = {f["rule_id"] for f in outcome.findings}
        assert "QUORUM-VOTE-001" in rules and "QUORUM-VOTE-002" in rules

    def test_usage_is_accounted(self) -> None:
        outcome = _run({NOVA: [_vote(0.1)], LLAMA: [_vote(0.1)]})
        assert outcome.usage["input"] == 240
        assert outcome.usage["output"] == 80

    def test_votes_carry_model_ids(self) -> None:
        outcome = _run({NOVA: [_vote(0.1)], LLAMA: [_vote(0.1)]})
        assert outcome.votes["adversary"]["model"] == LLAMA
        assert outcome.votes["reasoner"]["model"] == NOVA

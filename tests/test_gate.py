"""Veto suite for the deterministic gate (doc 05 section 4, ADR-001)."""

import pytest
from pydantic import BaseModel, ConfigDict

from antares.gate import run_gate
from antares.policy import Policy
from antares.registry import ToolRegistry, ToolSpec, UnknownTool, build_default_registry
from antares.schemas import ActionClass, VerdictState


class AttachPolicyParams(BaseModel):
    """Synthetic PERMISSION tool: IAM is not namespaced, the class still is."""

    model_config = ConfigDict(extra="forbid")
    role_name: str


PERMISSION_SPEC = ToolSpec(
    tool="iam.attach_policy",
    action="iam:AttachRolePolicy",
    action_class=ActionClass.PERMISSION,
    params_model=AttachPolicyParams,
    resource_fields={},
    description="synthetic permission-class tool for gate tests",
)


def _registry() -> ToolRegistry:
    return build_default_registry().with_tools([PERMISSION_SPEC])


def _call(tool: str, action: str, params: dict) -> dict:
    return {
        "call_id": "call-test-0001",
        "tool": tool,
        "action": action,
        "params": params,
        "session": {"session_id": "session-test-01"},
        "requested_by": "agent/test",
    }


def _outcome(tool: str, action: str, params: dict, policy: Policy | None = None):
    from antares.schemas import ToolCall

    call = ToolCall.model_validate(_call(tool, action, params))
    return run_gate(call, _registry(), policy or Policy())


class TestAllowPath:
    def test_clean_read_allows(self) -> None:
        outcome = _outcome(
            "ledger.describe", "dynamodb:DescribeTable", {"table": "antares-dev-ledger"}
        )
        assert outcome.state is VerdictState.ALLOW
        assert outcome.result.code_blocked is False

    def test_clean_write_allows(self) -> None:
        outcome = _outcome(
            "ledger.update_item",
            "dynamodb:UpdateItem",
            {
                "table": "antares-dev-ledger",
                "key": {"pk": "customer#4829"},
                "update_expression": "SET tier = :t",
            },
        )
        assert outcome.state is VerdictState.ALLOW

    def test_gate_is_fast(self) -> None:
        outcome = _outcome(
            "ledger.describe", "dynamodb:DescribeTable", {"table": "antares-dev-ledger"}
        )
        assert 0 <= outcome.gate_ms < 100


class TestVeto:
    def test_action_mismatch_blocks(self) -> None:
        outcome = _outcome("ledger.describe", "s3:DeleteBucket", {"table": "antares-dev-ledger"})
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-ACT-001" for f in outcome.result.findings)

    def test_schema_violation_blocks(self) -> None:
        outcome = _outcome(
            "ledger.update_item", "dynamodb:UpdateItem", {"table": "antares-dev-ledger"}
        )
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-SCH-001" for f in outcome.result.findings)

    def test_unknown_parameter_blocks(self) -> None:
        outcome = _outcome(
            "ledger.describe",
            "dynamodb:DescribeTable",
            {"table": "antares-dev-ledger", "force": True},
        )
        assert outcome.state is VerdictState.HARD_BLOCK

    def test_shell_metacharacter_blocks(self) -> None:
        outcome = _outcome(
            "ledger.update_item",
            "dynamodb:UpdateItem",
            {
                "table": "antares-dev-ledger",
                "key": {"pk": "a"},
                "update_expression": "SET tier = :v && tier2 = :w",
            },
        )
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-SHL-001" for f in outcome.result.findings)

    def test_destructive_pattern_blocks(self) -> None:
        outcome = _outcome(
            "vault.put_object",
            "s3:PutObject",
            {"bucket": "antares-dev-vault", "key": "notes/rm -rf.txt"},
        )
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-SHL-002" for f in outcome.result.findings)

    def test_outside_namespace_blocks(self) -> None:
        outcome = _outcome("ledger.describe", "dynamodb:DescribeTable", {"table": "prod-customers"})
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-ARN-001" for f in outcome.result.findings)

    def test_ssm_outside_prefix_blocks(self) -> None:
        outcome = _outcome(
            "config.put_parameter",
            "ssm:PutParameter",
            {"name": "/production/payments/endpoint", "value": "https://x"},
        )
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-ARN-001" for f in outcome.result.findings)

    def test_stack_of_blocks_reports_all(self) -> None:
        outcome = _outcome(
            "ledger.update_item",
            "dynamodb:UpdateItem",
            {
                "table": "prod-customers",
                "key": {"pk": "a"},
                "update_expression": "SET tier = :v && x = :y",
            },
        )
        rules = {f.rule_id for f in outcome.result.findings}
        assert {"GATE-ARN-001", "GATE-SHL-001"} <= rules
        assert outcome.result.code_blocked is True


class TestEscalation:
    def test_clean_destroy_abstains_pending_quorum(self) -> None:
        outcome = _outcome(
            "ledger.delete_item",
            "dynamodb:DeleteItem",
            {"table": "antares-dev-ledger", "key": {"pk": "customer#4829"}},
        )
        assert outcome.state is VerdictState.ABSTAIN
        assert any(f.rule_id == "GATE-ESC-001" for f in outcome.result.findings)

    def test_permission_class_abstains(self) -> None:
        outcome = _outcome("iam.attach_policy", "iam:AttachRolePolicy", {"role_name": "demo"})
        assert outcome.state is VerdictState.ABSTAIN

    def test_denied_class_hard_blocks_even_clean(self) -> None:
        policy = Policy(deny_classes=frozenset({"PERMISSION"}))
        outcome = _outcome(
            "iam.attach_policy", "iam:AttachRolePolicy", {"role_name": "demo"}, policy
        )
        assert outcome.state is VerdictState.HARD_BLOCK
        assert any(f.rule_id == "GATE-POL-001" for f in outcome.result.findings)


class TestUnknownTool:
    def test_unknown_tool_raises_to_gateway(self) -> None:
        with pytest.raises(UnknownTool):
            _outcome("ghost.tool", "ghost:Action", {})

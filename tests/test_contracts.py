"""Contract tests for schemas, registry and policy (docs 05, 06, 08)."""

import pytest
from pydantic import ValidationError

from antares.policy import Policy
from antares.registry import ToolRegistry, UnknownTool, build_default_registry
from antares.schemas import ActionClass, ToolCall, VerdictState


def _call(**overrides: object) -> dict:
    base: dict = {
        "call_id": "call-0001",
        "tool": "ledger.describe",
        "action": "dynamodb:DescribeTable",
        "params": {"table": "antares-dev-ledger"},
        "session": {"session_id": "session-0001"},
        "requested_by": "agent/test",
    }
    base.update(overrides)
    return base


class TestToolCall:
    def test_valid_call_parses(self) -> None:
        call = ToolCall.model_validate(_call())
        assert call.tool == "ledger.describe"
        assert call.session.trust_score == 0.0

    def test_unknown_fields_are_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall.model_validate(_call(sneaky_field="hello"))

    def test_bad_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall.model_validate(_call(session={"session_id": "short"}))


class TestPolicy:
    def test_class_weights_match_doc06(self) -> None:
        policy = Policy()
        assert policy.class_weights == {
            "READ": 0.0, "WRITE": 0.3, "PERMISSION": 0.8, "DESTROY": 1.0,
        }

    def test_escalate_classes_match_doc05(self) -> None:
        policy = Policy()
        assert policy.escalate_classes == frozenset({"DESTROY", "PERMISSION"})

    def test_from_env_overrides_namespace(self) -> None:
        policy = Policy.from_env({
            "ANTARES_ALLOWED_TABLES": "prod-main",
            "ANTARES_ALLOWED_BUCKETS": "prod-vault",
            "ANTARES_SSM_PREFIX": "/antares/prod/",
            "ANTARES_DENY_CLASSES": "DESTROY",
        })
        assert policy.allowed_tables == frozenset({"prod-main"})
        assert policy.allowed_buckets == frozenset({"prod-vault"})
        assert policy.allowed_ssm_prefix == "/antares/prod/"
        assert policy.deny_classes == frozenset({"DESTROY"})

    def test_frozen_policy_cannot_drift(self) -> None:
        import dataclasses

        policy = Policy()
        with pytest.raises(dataclasses.FrozenInstanceError):
            policy.version = "p2"  # type: ignore[misc]


class TestRegistry:
    def test_default_registry_covers_three_classes(self) -> None:
        # PERMISSION has no sandbox tool (IAM is not namespaced); the gate's
        # PERMISSION handling is exercised with a synthetic spec in test_gate.
        registry = build_default_registry()
        classes = {registry.get(name).action_class for name in registry.names()}
        assert classes == {ActionClass.READ, ActionClass.WRITE, ActionClass.DESTROY}

    def test_unknown_tool_raises_unknown_tool(self) -> None:
        registry = ToolRegistry({})
        with pytest.raises(UnknownTool):
            registry.get("nope.nothing")

    def test_every_param_schema_forbids_extra(self) -> None:
        registry = build_default_registry()
        for name in registry.names():
            spec = registry.get(name)
            assert spec.params_model.model_config.get("extra") == "forbid", name

    def test_resource_fields_declared_for_cloud_touching_params(self) -> None:
        # Every tool that touches a table or bucket declares the field.
        registry = build_default_registry()
        assert registry.get("ledger.put_item").resource_fields == {"table": "table"}
        assert registry.get("vault.delete_objects").resource_fields == {"bucket": "bucket"}
        assert registry.get("config.put_parameter").resource_fields == {"name": "ssm_path"}


class TestVerdictStates:
    def test_three_states_only(self) -> None:
        assert {state.value for state in VerdictState} == {"ALLOW", "HARD_BLOCK", "ABSTAIN"}

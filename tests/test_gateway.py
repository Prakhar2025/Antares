"""Gateway tests with injected fakes (doc 14: fakes mirror real shapes)."""

import json

import pytest

from antares.gateway import create_app
from antares.policy import Policy
from antares.registry import build_default_registry


class FakeDynamo:
    """Mirrors transact_write_items and get_item semantics (ledger lesson, doc 14)."""

    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}

    def transact_write_items(self, TransactItems: list) -> dict:  # noqa: N803
        for entry in TransactItems:
            put = entry["Put"]
            item = put["Item"]
            self.items[(item["pk"]["S"], item["sk"]["S"])] = item
        return {}

    def get_item(self, TableName: str, Key: dict) -> dict:  # noqa: N803
        item = self.items.get((Key["pk"]["S"], Key["sk"]["S"]))
        return {"Item": item} if item else {}


def _event(method: str, path: str, body: dict | None = None) -> dict:
    event: dict = {"httpMethod": method, "path": path, "isBase64Encoded": False}
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def _call(tool: str, action: str, params: dict) -> dict:
    return {
        "call_id": "call-gw-0001",
        "tool": tool,
        "action": action,
        "params": params,
        "session": {"session_id": "session-gw-001"},
        "requested_by": "agent/test",
    }


@pytest.fixture()
def fake_ddb() -> FakeDynamo:
    return FakeDynamo()


@pytest.fixture()
def app(fake_ddb: FakeDynamo):
    return create_app(
        policy=Policy(),
        registry=build_default_registry(),
        ddb=fake_ddb,
        table_name="antares-dev-main",
        halt=False,
        metrics=None,
    )


class TestGateRoute:
    def test_clean_read_returns_allow_and_persists(self, app, fake_ddb) -> None:
        response = app(_event("POST", "/v1/gate", _call(
            "ledger.describe", "dynamodb:DescribeTable", {"table": "antares-dev-ledger"}
        )))
        assert response["statusCode"] == 200
        verdict = json.loads(response["body"])
        assert verdict["state"] == "ALLOW"
        assert verdict["latency_ms"]["total"] >= 0
        assert verdict["schema_version"] == "v1"
        # dual-write: a verdict lookup item and a state feed item
        assert len(fake_ddb.items) == 2
        lookup = fake_ddb.items[(f"VERDICT#{verdict['verdict_id']}", "META")]
        assert lookup["verdict_id"]["S"] == verdict["verdict_id"]
        assert int(lookup["ttl"]["N"]) > 0
        feed = next(item for key, item in fake_ddb.items.items() if key[0] == "STATE#ALLOW")
        assert feed["action_class"]["S"] == "READ"

    def test_destructive_class_abstains(self, app) -> None:
        response = app(_event("POST", "/v1/gate", _call(
            "ledger.delete_item", "dynamodb:DeleteItem",
            {"table": "antares-dev-ledger", "key": {"pk": "customer#4829"}},
        )))
        verdict = json.loads(response["body"])
        assert verdict["state"] == "ABSTAIN"

    def test_shell_metachar_hard_blocks(self, app) -> None:
        response = app(_event("POST", "/v1/gate", _call(
            "ledger.update_item", "dynamodb:UpdateItem",
            {"table": "antares-dev-ledger", "key": {"pk": "a"},
             "update_expression": "SET tier = :v && x = :y"},
        )))
        verdict = json.loads(response["body"])
        assert verdict["state"] == "HARD_BLOCK"
        assert any(f["rule_id"] == "GATE-SHL-001" for f in verdict["gate"]["findings"])

    def test_unknown_tool_is_404_problem(self, app, fake_ddb) -> None:
        response = app(_event("POST", "/v1/gate", _call(
            "ghost.tool", "ghost:Action", {},
        )))
        assert response["statusCode"] == 404
        assert json.loads(response["body"])["code"] == "unknown-tool"
        assert len(fake_ddb.items) == 0

    def test_invalid_body_is_422_problem(self, app) -> None:
        response = app({"httpMethod": "POST", "path": "/v1/gate", "body": "{not json"})
        assert response["statusCode"] == 422
        assert json.loads(response["body"])["code"] == "schema-rejected"

    def test_missing_fields_are_422(self, app) -> None:
        response = app(_event("POST", "/v1/gate", {"tool": "ledger.describe"}))
        assert response["statusCode"] == 422
        assert json.loads(response["body"])["code"] == "schema-rejected"


class TestDecisionRoute:
    def test_fetch_persisted_decision(self, app, fake_ddb) -> None:
        created = app(_event("POST", "/v1/gate", _call(
            "ledger.describe", "dynamodb:DescribeTable", {"table": "antares-dev-ledger"}
        )))
        verdict = json.loads(created["body"])
        fetched = app(_event("GET", f"/v1/decisions/{verdict['verdict_id']}"))
        assert fetched["statusCode"] == 200
        assert json.loads(fetched["body"])["verdict_id"] == verdict["verdict_id"]

    def test_missing_decision_is_404(self, app) -> None:
        response = app(_event("GET", "/v1/decisions/does-not-exist"))
        assert response["statusCode"] == 404
        assert json.loads(response["body"])["code"] == "verdict-not-found"


class TestHaltAndRouting:
    def test_halt_returns_503_kernel_halted(self, fake_ddb) -> None:
        halted = create_app(
            policy=Policy(), registry=build_default_registry(), ddb=fake_ddb,
            table_name="antares-dev-main", halt=True, metrics=None,
        )
        response = halted(_event("POST", "/v1/gate", _call(
            "ledger.describe", "dynamodb:DescribeTable", {"table": "antares-dev-ledger"}
        )))
        assert response["statusCode"] == 503
        assert json.loads(response["body"])["code"] == "kernel-halted"

    def test_unknown_route_is_404(self, app) -> None:
        response = app(_event("GET", "/v1/nothing"))
        assert response["statusCode"] == 404

    def test_options_preflight_is_204(self, app) -> None:
        response = app(_event("OPTIONS", "/v1/gate"))
        assert response["statusCode"] == 204

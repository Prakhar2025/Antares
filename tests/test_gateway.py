"""Gateway tests with injected fakes (doc 14: fakes mirror real shapes)."""

import json

import pytest

from antares.gateway import create_app
from antares.policy import Policy
from antares.registry import build_default_registry


class FakeDynamo:
    """Mirrors boto3 put_item/query semantics (ledger lesson, doc 14)."""

    def __init__(self) -> None:
        self.items: list[tuple[str, dict]] = []

    def put_item(self, TableName: str, Item: dict) -> dict:  # noqa: N803
        self.items.append((TableName, Item))
        return {}

    def query(self, **kwargs: object) -> dict:
        values = kwargs.get("ExpressionAttributeValues") or {}
        wanted = values.get(":v", {}).get("S")
        matches = [item for _, item in self.items if item.get("verdict_id", {}).get("S") == wanted]
        return {"Items": matches}


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
        assert len(fake_ddb.items) == 1
        table, item = fake_ddb.items[0]
        assert table == "antares-dev-main"
        assert item["pk"]["S"] == "TENANT#default"
        assert item["sk"]["S"].startswith("DECISION#")
        assert item["state"]["S"] == "ALLOW"
        assert int(item["ttl"]["N"]) > 0

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

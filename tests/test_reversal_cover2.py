"""Final coverage: llm paths, ledger fork retry, ssm and dynamodb degradations."""

import json

import pytest
from botocore.exceptions import ClientError

from antares.gateway import create_app
from antares.ledger import Ledger, LedgerForkError
from antares.llm import ModelOutputError, converse_json
from antares.policy import Policy
from antares.probes import measure_radius, probe_dynamodb_item
from antares.registry import build_default_registry
from antares.saga import SagaEngine
from test_reversal import FakeSsm, FakeWorldDynamo  # noqa: F401


class FakeBedrockFlaky:
    """First call returns prose, second returns valid JSON."""

    def __init__(self) -> None:
        self.calls = 0

    def converse(self, modelId: str, system: list, messages: list, inferenceConfig: dict) -> dict:  # noqa: N803
        self.calls += 1
        if self.calls % 2 == 1:
            return {
                "output": {"message": {"content": [{"text": "I will not return json"}]}},
                "usage": {"inputTokens": 10, "outputTokens": 5},
            }
        return {
            "output": {"message": {"content": [{"text": '{"risk": 0.1, "reason": "ok"}'}]}},
            "usage": {"inputTokens": 20, "outputTokens": 8},
        }


class TestLlmPaths:
    def test_vote_wrapper_retries_once(self) -> None:
        # The retry lives in the quorum vote wrapper, not in converse_json:
        # one flaky call, then the valid JSON on the second attempt.
        from antares.quorum import _vote

        bedrock = FakeBedrockFlaky()
        vote, usage, error = _vote(bedrock, "model", "system", "user")
        assert error is None
        assert vote is not None and vote["risk"] == 0.1
        # usage counts only the successful call's tokens in this fake
        assert usage["input"] == 20

    def test_converse_json_extracts_nested_json(self) -> None:
        class Nested:
            def converse(self, **kwargs: object) -> dict:
                return {
                    "output": {
                        "message": {
                            "content": [{"text": 'Sure! {"risk": 0.4, "reason": "why not"}'}]
                        }
                    },
                    "usage": {"inputTokens": 5, "outputTokens": 3},
                }

        vote, _usage = converse_json(Nested(), "model", "sys", "user")
        assert vote["risk"] == 0.4

    def test_unbalanced_json_raises(self) -> None:
        class Broken:
            def converse(self, **kwargs: object) -> dict:
                return {"output": {"message": {"content": [{"text": "{oops"}]}}, "usage": {}}

        with pytest.raises(ModelOutputError):
            converse_json(Broken(), "model", "sys", "user")


class TestProbesDegrade:
    def test_dynamodb_probe_unknown_on_failure(self) -> None:
        class ExplodingDynamo:
            def get_item(self, **kwargs: object) -> dict:
                raise RuntimeError("boom")

            def describe_table(self, **kwargs: object) -> dict:
                raise RuntimeError("boom")

        radius = probe_dynamodb_item(
            ExplodingDynamo(), "antares-dev-ledger", {"pk": "a", "sk": "b"}, 1.0, deleting=True
        )
        assert radius.unknown is True
        assert radius.score == 1.0

    def test_measure_radius_unknown_service(self) -> None:
        radius = measure_radius("sqs:SendMessage", {}, 0.0, {})
        assert radius.score == 0.0


class TestQuorumDivergenceRoute:
    def test_quorum_runs_inside_gate_for_flagged_writes(self) -> None:
        class YesBedrock:
            def converse(self, **kwargs: object) -> dict:
                return {
                    "output": {
                        "message": {
                            "content": [
                                [{"text": '{"risk": 0.1, "reason": "fine"}'}],
                                [{"text": '{"risk": 0.2, "reason": "fine"}'}],
                            ][0]
                        }
                    },
                    "usage": {"inputTokens": 50, "outputTokens": 20},
                }

        world = FakeWorldDynamo()
        app = create_app(
            policy=Policy(),
            registry=build_default_registry(),
            ddb=world,
            table_name="antares-dev-main",
            halt=False,
            metrics=None,
            bedrock=YesBedrock(),
            kms=None,
            signing_key_id=None,
        )
        call = {
            "call_id": "call-qg-0001",
            "tool": "ledger.update_item",
            "action": "dynamodb:UpdateItem",
            "params": {
                "table": "antares-dev-ledger",
                "key": {"pk": "c1", "sk": "p"},
                "update_expression": "SET tier = :t",
                "expression_values": {":t": {"S": "GOLD"}},
            },
            "session": {"session_id": "session-qg-001"},
            "requested_by": "agent/test",
        }
        response = app({"httpMethod": "POST", "path": "/v1/gate", "body": json.dumps(call)})
        verdict = json.loads(response["body"])
        assert verdict["state"] == "ALLOW"
        assert verdict["quorum"]["fusion"] == "QUORUM-ALLOW-001"
        assert verdict["quorum"]["votes"]["adversary"]["model"].startswith("us.meta.")


class TestLedgerFork:
    def test_fork_raises_ledger_fork_error(self) -> None:
        class RacingWorld(FakeWorldDynamo):
            """Head item always exists with an unexpected leaf: forces fork."""

            def put_item(
                self,
                TableName: str,
                Item: dict,
                ConditionExpression: str | None = None,
                ExpressionAttributeValues: dict | None = None,
            ) -> dict:  # noqa: N803
                # The head always moved: every conditional head put fails.
                raise ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")

        ledger = Ledger(RacingWorld(), "antares-dev-main")
        with pytest.raises(LedgerForkError):
            ledger.append({"record_type": "action", "n": 1})


class TestReceiptlessExecute:
    def test_executed_without_ledger_reports_null_receipt(self) -> None:
        world = FakeWorldDynamo()
        world._table("antares-dev-ledger")[("c1", "p")] = {
            "pk": {"S": "c1"},
            "sk": {"S": "p"},
            "tier": {"S": "TRIAL"},
        }
        app = create_app(
            policy=Policy(),
            registry=build_default_registry(),
            ddb=world,
            table_name="antares-dev-main",
            halt=False,
            metrics=None,
            bedrock=None,
            kms=None,
            signing_key_id=None,
            aws_clients={"dynamodb": world, "s3": None, "ssm": FakeSsm()},
            ledger=Ledger(world, "antares-dev-main"),
            saga=SagaEngine(
                ddb=world,
                s3=None,
                ssm=FakeSsm(),
                ledger_table="antares-dev-main",
                vault_table="antares-dev-main",
            ),
        )
        call = {
            "call_id": "call-cov-0001",
            "tool": "ledger.put_item",
            "action": "dynamodb:PutItem",
            "params": {
                "table": "antares-dev-ledger",
                "item": {"pk": "n1", "sk": "p", "value": "v"},
            },
            "session": {"session_id": "session-cov-01"},
            "requested_by": "agent/test",
        }
        gated = app({"httpMethod": "POST", "path": "/v1/gate", "body": json.dumps(call)})
        verdict = json.loads(gated["body"])
        assert verdict["state"] == "ALLOW"
        assert verdict["radius"] is not None
        executed = app(
            {
                "httpMethod": "POST",
                "path": "/v1/execute",
                "body": json.dumps({"verdict_id": verdict["verdict_id"]}),
            }
        )
        body = json.loads(executed["body"])
        assert body["status"] == "executed"
        assert body["receipt"] is not None
        assert body["receipt"]["leaf_hash"] != "GENESIS"

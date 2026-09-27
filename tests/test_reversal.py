"""Reversal milestone tests: probes, blast radius, saga cycles, ledger chain.

FakeWorldDynamo is a behavioral fake: it stores typed items and mirrors
the exact operations the saga uses (doc 14: fakes mirror real shapes).
"""

import json

from botocore.exceptions import ClientError

from antares.gateway import create_app
from antares.ledger import Ledger
from antares.policy import Policy
from antares.probes import probe_dynamodb_item, probe_ssm_parameter
from antares.registry import build_default_registry
from antares.saga import SagaEngine, item_hash


class FakeWorldDynamo:
    """Behavioral DynamoDB fake with typed storage and real semantics."""

    def __init__(self) -> None:
        self.tables: dict[str, dict[tuple[str, str], dict]] = {}

    def _table(self, name: str) -> dict[tuple[str, str], dict]:
        return self.tables.setdefault(name, {})

    @staticmethod
    def _k(Key: dict) -> tuple[str, str]:  # noqa: N803
        return (Key["pk"]["S"], Key["sk"]["S"])

    def get_item(self, TableName: str, Key: dict, ConsistentRead: bool = False) -> dict:  # noqa: N803
        item = self._table(TableName).get(self._k(Key))
        return {"Item": item} if item else {}

    def put_item(
        self,
        TableName: str,
        Item: dict,
        ConditionExpression: str | None = None,
        ExpressionAttributeValues: dict | None = None,
    ) -> dict:  # noqa: N803
        key = self._k(Item)
        table = self._table(TableName)
        if ConditionExpression and "leaf_hash = :expected" in ConditionExpression:
            # ledger head semantics: genesis passes, unchanged head passes
            expected = (ExpressionAttributeValues or {}).get(":expected", {}).get("S", "")
            head = table.get(key)
            if head and head["leaf_hash"]["S"] != expected:
                raise ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")
        elif ConditionExpression and "attribute_not_exists" in ConditionExpression and key in table:
            raise ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")
        table[key] = Item
        return {}

    def delete_item(self, TableName: str, Key: dict) -> dict:  # noqa: N803
        self._table(TableName).pop(self._k(Key), None)
        return {}

    def update_item(self, **kwargs: object) -> dict:
        table = self._table(kwargs["TableName"])
        key = self._k(kwargs["Key"])
        expression = kwargs.get("UpdateExpression", "")
        values = kwargs.get("ExpressionAttributeValues", {})
        names = kwargs.get("ExpressionAttributeNames", {})
        if "ADD" in expression and key not in table:
            table[key] = {}
        if key not in table:
            raise ClientError({"Error": {"Code": "ValidationException"}}, "UpdateItem")
        item = table[key]
        if "ADD" in expression:
            for name in values:
                attr = name.lstrip(":")
                addend = values[name]
                addend_num = (
                    float(addend.get("N", "0")) if isinstance(addend, dict) else float(addend)
                )
                current = item.get(attr, {"N": "0"})
                current["N"] = str(float(current.get("N", "0")) + addend_num)
            return {}
        if "SET" in expression:
            for part in expression.split("SET", 1)[1].split(","):
                attr_part, placeholder = part.strip().split(" = ", 1)
                attr = attr_part.strip()
                if attr.startswith("#"):
                    attr = names.get(attr, attr).lstrip("#")
                item[attr] = values[placeholder]
            return {}

    def describe_table(self, TableName: str) -> dict:  # noqa: N803
        return {"Table": {"ItemCount": len(self._table(TableName))}}

    def describe_continuous_backups(self, TableName: str) -> dict:  # noqa: N803
        return {
            "ContinuousBackupsDescription": {
                "ContinuousBackupsStatus": "ENABLED",
                "PointInTimeRecoveryDescription": {"PointInTimeRecoveryStatus": "ENABLED"},
            }
        }

    def transact_write_items(self, TransactItems: list) -> dict:  # noqa: N803
        for entry in TransactItems:
            if "Put" in entry:
                self.put_item(TableName=entry["Put"]["TableName"], Item=entry["Put"]["Item"])
            elif "ConditionCheck" in entry:
                check = entry["ConditionCheck"]
                key = self._k(check["Key"])
                table = self._table(check["TableName"])
                expression = check.get("ConditionExpression", "")
                if "leaf_hash = :expected" in expression:
                    # ledger head: passes when absent (genesis) or unchanged
                    head = table.get(key)
                    expected = check["ExpressionAttributeValues"][":expected"]["S"]
                    ok = head is None or head["leaf_hash"]["S"] == expected
                else:
                    ok = key not in table
                if not ok:
                    raise ClientError(
                        {"Error": {"Code": "TransactionCanceledException"}},
                        "TransactWriteItems",
                    )
            elif "Update" in entry:
                update = dict(entry["Update"])
                update.setdefault("UpdateExpression", "SET bypassed = :b")
                update["ExpressionAttributeValues"] = update.get(
                    "ExpressionAttributeValues", {":b": {"BOOL": True}}
                )
                self.update_item(**update)
        return {}

    def query(self, **kwargs: object) -> dict:
        values = kwargs.get("ExpressionAttributeValues") or {}
        prefix = values.get(":p", {}).get("S", "")
        table = self._table(kwargs["TableName"])
        matches = [item for (pk, sk), item in table.items() if pk == prefix]
        matches.sort(key=lambda item: item.get("sk", {}).get("S", ""), reverse=True)
        return {"Items": matches[: kwargs.get("Limit", 100)]}


class FakeSsm:
    """Mirrors SSM parameter semantics with version history."""

    def __init__(self) -> None:
        self.parameters: dict[str, dict] = {}

    def get_parameter(self, Name: str, WithDecryption: bool = False) -> dict:  # noqa: N803
        if Name not in self.parameters:
            raise self.exceptions.ParameterNotFound()
        return {"Parameter": {"Name": Name, **self.parameters[Name]}}

    def put_parameter(self, Name: str, Value: str, Type: str, Overwrite: bool) -> dict:  # noqa: N803
        if Name in self.parameters and not Overwrite:
            raise ClientError({"Error": {"Code": "ParameterAlreadyExists"}}, "PutParameter")
        version = self.parameters.get(Name, {}).get("Version", 0) + 1
        self.parameters[Name] = {"Value": Value, "Type": Type, "Version": version}
        return {"Version": version}

    class exceptions:  # noqa: N801
        class ParameterNotFound(Exception):
            pass


class TestSagaCycle:
    def _engine(self, world: FakeWorldDynamo) -> SagaEngine:
        return SagaEngine(
            ddb=world,
            s3=None,
            ssm=FakeSsm(),
            ledger_table="antares-dev-main",
            vault_table="antares-dev-main",
        )

    def test_delete_and_rollback_restores_byte_identity(self) -> None:
        world = FakeWorldDynamo()
        ledger_table = world._table("antares-dev-ledger")
        seed = {
            "pk": {"S": "customer#4829"},
            "sk": {"S": "profile"},
            "tier": {"S": "ENTERPRISE"},
            "billing_status": {"S": "ACTIVE"},
        }
        ledger_table[("customer#4829", "profile")] = seed
        params = {"table": "antares-dev-ledger", "key": {"pk": "customer#4829", "sk": "profile"}}

        result = self._engine(world).execute("dynamodb:DeleteItem", params, "act-1")
        assert result.committed is True
        assert result.prior_hash == item_hash(
            {
                "pk": "customer#4829",
                "sk": "profile",
                "tier": "ENTERPRISE",
                "billing_status": "ACTIVE",
            }
        )
        assert ("customer#4829", "profile") not in ledger_table

        rolled = self._engine(world).rollback("dynamodb:DeleteItem", params, "act-1")
        assert rolled.rolled_back is True
        assert rolled.rollback_verified is True
        assert ("customer#4829", "profile") in ledger_table
        assert ledger_table[("customer#4829", "profile")]["tier"]["S"] == "ENTERPRISE"

    def test_update_and_rollback_restores_prior_value(self) -> None:
        world = FakeWorldDynamo()
        ledger_table = world._table("antares-dev-ledger")
        ledger_table[("c1", "p")] = {"pk": {"S": "c1"}, "sk": {"S": "p"}, "tier": {"S": "BASIC"}}
        params = {
            "table": "antares-dev-ledger",
            "key": {"pk": "c1", "sk": "p"},
            "update_expression": "SET tier = :t",
            "expression_values": {":t": {"S": "SUSPENDED"}},
        }
        engine = self._engine(world)
        engine.execute("dynamodb:UpdateItem", params, "act-2")
        assert ledger_table[("c1", "p")]["tier"]["S"] == "SUSPENDED"
        rolled = engine.rollback("dynamodb:UpdateItem", params, "act-2")
        assert rolled.rollback_verified is True
        assert ledger_table[("c1", "p")]["tier"]["S"] == "BASIC"

    def test_no_vault_entry_means_no_rollback_claim(self) -> None:
        world = FakeWorldDynamo()
        result = self._engine(world).rollback(
            "dynamodb:DeleteItem",
            {"table": "antares-dev-ledger", "key": {"pk": "x", "sk": "y"}},
            "act-none",
        )
        # prior state unknown: the engine reports honestly, no false verify
        assert result.prior_image is None


class TestProbes:
    def test_probe_measures_existing_item_with_pitr(self) -> None:
        world = FakeWorldDynamo()
        world._table("antares-dev-ledger")[("c1", "p")] = {"pk": {"S": "c1"}, "sk": {"S": "p"}}
        radius = probe_dynamodb_item(
            world, "antares-dev-ledger", {"pk": "c1", "sk": "p"}, 1.0, deleting=True
        )
        assert radius.resources_at_risk == 1
        assert radius.reversibility <= 0.5
        assert radius.score == round(1 * 1.0 * (1 - radius.reversibility), 4)

    def test_probe_missing_item_scores_zero(self) -> None:
        world = FakeWorldDynamo()
        radius = probe_dynamodb_item(
            world, "antares-dev-ledger", {"pk": "ghost", "sk": "p"}, 1.0, deleting=True
        )
        assert radius.resources_at_risk == 0
        assert radius.score == 0.0

    def test_probe_ssm_existing_parameter(self) -> None:
        ssm = FakeSsm()
        ssm.put_parameter(Name="/antares/dev/x", Value="v1", Type="String", Overwrite=False)
        radius = probe_ssm_parameter(ssm, "/antares/dev/x", 0.3, writing=True)
        assert radius.resources_at_risk == 1
        assert radius.reversibility == 0.8


class TestLedger:
    def test_chain_links_and_verification(self) -> None:
        world = FakeWorldDynamo()
        ledger = Ledger(world, "antares-dev-main")
        receipts = [ledger.append({"n": n, "ts": f"t{n}"}) for n in range(3)]
        assert receipts[0].prev_leaf_hash == "GENESIS"
        assert receipts[1].prev_leaf_hash == receipts[0].leaf_hash
        assert receipts[2].prev_leaf_hash == receipts[1].leaf_hash
        for receipt in receipts:
            assert ledger.verify_record(receipt.record, receipt.leaf_hash) is True

    def test_tampered_record_fails_verification(self) -> None:
        world = FakeWorldDynamo()
        ledger = Ledger(world, "antares-dev-main")
        receipt = ledger.append({"n": 1})
        tampered = {**receipt.record, "n": 2}
        assert ledger.verify_record(tampered, receipt.leaf_hash) is False


class TestExecuteRoute:
    def test_full_execute_flow_with_fakes(self) -> None:
        world = FakeWorldDynamo()
        world._table("antares-dev-ledger")[("c9", "p")] = {
            "pk": {"S": "c9"},
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
            "call_id": "call-ex-0001",
            "tool": "ledger.delete_item",
            "action": "dynamodb:DeleteItem",
            "params": {"table": "antares-dev-ledger", "key": {"pk": "c9", "sk": "p"}},
            "session": {"session_id": "session-ex-001"},
            "requested_by": "agent/test",
        }
        # gate first (ALLOW needs quorum for DESTROY... bedrock None keeps ABSTAIN)
        gated = app({"httpMethod": "POST", "path": "/v1/gate", "body": json.dumps(call)})
        verdict = json.loads(gated["body"])
        assert verdict["state"] == "ABSTAIN"
        # approve via direct ledger surgery (bypass tested separately), then execute
        world._table("antares-dev-main")[(f"VERDICT#{verdict['verdict_id']}", "META")]["state"] = {
            "S": "ALLOW"
        }
        world._table("antares-dev-main")[(f"VERDICT#{verdict['verdict_id']}", "META")][
            "bypassed"
        ] = {"BOOL": True}

        executed = app(
            {
                "httpMethod": "POST",
                "path": "/v1/execute",
                "body": json.dumps({"verdict_id": verdict["verdict_id"]}),
            }
        )
        body = json.loads(executed["body"])
        assert body["status"] == "executed"
        assert body["saga"]["prior_hash"] != "empty"
        assert ("c9", "p") not in world._table("antares-dev-ledger")
        assert body["receipt"] is not None

        replayed = app(
            {
                "httpMethod": "POST",
                "path": "/v1/execute",
                "body": json.dumps({"verdict_id": verdict["verdict_id"]}),
            }
        )
        assert replayed["statusCode"] == 403

        rolled = app(
            {"httpMethod": "POST", "path": f"/v1/actions/{verdict['verdict_id']}/rollback"}
        )
        rolled_body = json.loads(rolled["body"])
        assert rolled_body["status"] == "rolled_back"
        assert rolled_body["verified"] is True
        assert ("c9", "p") in world._table("antares-dev-ledger")

        receipt = app({"httpMethod": "GET", "path": f"/v1/actions/{verdict['verdict_id']}/receipt"})
        assert receipt["statusCode"] == 200

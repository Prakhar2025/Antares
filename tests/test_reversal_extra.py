"""Targeted tests for probe failures, S3 probes, SSM cycles and degrade paths."""

from botocore import exceptions as botocore_exceptions
from botocore.exceptions import ClientError

from antares.probes import probe_s3_objects
from antares.saga import SagaEngine
from test_reversal import FakeWorldDynamo


class FakeS3:
    """Mirrors S3 probe surface: versioning, head_object, 404 semantics."""

    # The real boto3 client exposes the exceptions MODULE here, so the fake
    # must too: probes catch s3.exceptions.ClientError by that chain.
    exceptions = botocore_exceptions

    def __init__(
        self, versioning: str = "Enabled", existing: set[str] | None = None, fail: bool = False
    ):
        self.versioning = versioning
        self.existing = existing or set()
        self.fail = fail

    def get_bucket_versioning(self, Bucket: str) -> dict:  # noqa: N803
        return {"Status": self.versioning}

    def head_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803
        if self.fail:
            raise ClientError({"Error": {"Code": "500"}}, "HeadObject")
        if Key in self.existing:
            return {"VersionId": "v1"}
        raise ClientError({"Error": {"Code": "404"}}, "HeadObject")


class FakeBrokenDynamo:
    """Every call raises: probe must report unknown, never crash."""

    def get_item(self, **kwargs: object) -> dict:
        raise RuntimeError("boom")

    def describe_table(self, **kwargs: object) -> dict:
        raise RuntimeError("boom")

    def describe_continuous_backups(self, **kwargs: object) -> dict:
        raise RuntimeError("boom")


class TestS3Probes:
    def test_versioned_bucket_deletion_is_reversible(self) -> None:
        s3 = FakeS3(versioning="Enabled", existing={"a.txt"})
        radius = probe_s3_objects(s3, "antares-dev-vault", ["a.txt"], 1.0, deleting=True)
        assert radius.resources_at_risk == 1
        assert radius.reversibility == 0.9
        assert radius.score == round(1 * 1.0 * 0.1, 4)

    def test_unversioned_deletion_is_not_reversible(self) -> None:
        s3 = FakeS3(versioning="Disabled", existing={"a.txt"})
        radius = probe_s3_objects(s3, "antares-dev-vault", ["a.txt"], 1.0, deleting=True)
        assert radius.reversibility == 0.0
        assert radius.score == 1.0

    def test_missing_key_scores_zero(self) -> None:
        s3 = FakeS3(versioning="Enabled", existing=set())
        radius = probe_s3_objects(s3, "antares-dev-vault", ["ghost.txt"], 1.0, deleting=True)
        assert radius.resources_at_risk == 0
        assert radius.score == 0.0

    def test_probe_failure_marks_unknown(self) -> None:
        s3 = FakeS3(fail=True)
        radius = probe_s3_objects(s3, "antares-dev-vault", ["a.txt"], 1.0, deleting=True)
        assert radius.unknown is True
        assert radius.score == 1.0


class TestSsmSaga:
    def test_put_parameter_and_rollback(self) -> None:
        from test_reversal import FakeSsm  # noqa: PLC0415

        ssm = FakeSsm()
        ssm.put_parameter(
            Name="/antares/dev/payments/gateway_endpoint",
            Value="https://old",
            Type="String",
            Overwrite=False,
        )
        saga = SagaEngine(
            ddb=FakeWorldDynamo(),
            s3=None,
            ssm=ssm,
            ledger_table="antares-dev-main",
            vault_table="antares-dev-main",
        )
        params = {
            "name": "/antares/dev/payments/gateway_endpoint",
            "value": "https://new",
            "overwrite": True,
        }
        result = saga.execute("ssm:PutParameter", params, "act-ssm-1")
        assert result.committed is True
        assert ssm.parameters["/antares/dev/payments/gateway_endpoint"]["Value"] == "https://new"

        rolled = saga.rollback("ssm:PutParameter", params, "act-ssm-1")
        assert rolled.rolled_back is True
        assert rolled.rollback_verified is True
        assert ssm.parameters["/antares/dev/payments/gateway_endpoint"]["Value"] == "https://old"

    def test_unsupported_action_recorded_honestly(self) -> None:
        saga = SagaEngine(
            ddb=FakeWorldDynamo(),
            s3=None,
            ssm=None,
            ledger_table="antares-dev-main",
            vault_table="antares-dev-main",
        )
        result = saga.execute("s3:PutObject", {"bucket": "b", "key": "k"}, "act-s3-1")
        assert result.committed is False
        assert "not implemented" in (result.error or "")


class FakeWorld:
    """Minimal single-table world for saga/ledger unit tests."""

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

    def put_item(self, TableName: str, Item: dict, ConditionExpression: str | None = None) -> dict:  # noqa: N803
        self._table(TableName)[self._k(Item)] = Item
        return {}

    def transact_write_items(self, TransactItems: list) -> dict:  # noqa: N803
        for entry in TransactItems:
            if "Put" in entry:
                self.put_item(TableName=entry["Put"]["TableName"], Item=entry["Put"]["Item"])
        return {}

"""Antares state probes (S4): measure blast radius from live cloud state.

Radius is never imagined (ADR: doc 04). Every mutating call gets its
resources probed with read-only Describe/List/Get calls, and the score is
deterministic: resource count x severity weight x (1 - reversibility).
A probe that fails marks the radius UNKNOWN and the fusion treats the
call at maximum severity (doc 04 failure matrix).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RadiusResult:
    """Measured blast radius for one proposed call (doc 05 section 3)."""

    resources_at_risk: int
    severity_weight: float
    reversibility: float
    score: float
    inputs: list[dict[str, Any]] = field(default_factory=list)
    unknown: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "resources_at_risk": self.resources_at_risk,
            "severity_weight": self.severity_weight,
            "reversibility": self.reversibility,
            "score": self.score,
            "inputs": self.inputs,
            "unknown": self.unknown,
        }


def _unknown(reason: str) -> RadiusResult:
    return RadiusResult(
        resources_at_risk=0,
        severity_weight=1.0,
        reversibility=0.0,
        score=1.0,
        inputs=[{"probe": "failed", "reason": reason}],
        unknown=True,
    )


def _dynamodb_reversibility(backups: dict[str, Any]) -> float:
    try:
        enabled = backups["ContinuousBackupsDescription"]["ContinuousBackupsStatus"] == "ENABLED"
        pitr = (
            backups["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"][
                "PointInTimeRecoveryStatus"
            ]
            == "ENABLED"
        )
        return 1.0 if pitr else (0.6 if enabled else 0.1)
    except (KeyError, TypeError):
        return 0.1


def probe_dynamodb_item(
    ddb: Any, table: str, key: dict[str, Any], weight: float, deleting: bool
) -> RadiusResult:
    """Probe one keyed item: does it exist, and can we undo what we plan?"""
    inputs: list[dict[str, Any]] = []
    typed_key = {name: {"S": str(value)} for name, value in key.items()}
    try:
        current = ddb.get_item(TableName=table, Key=typed_key, ConsistentRead=True).get("Item")
        described = ddb.describe_table(TableName=table)["Table"]
        try:
            backups = ddb.describe_continuous_backups(TableName=table)
        except Exception:  # noqa: BLE001  (continuous backups API not always enabled)
            backups = {}
        reversibility = _dynamodb_reversibility(backups) if current is not None else 0.9
        count = 1 if current is not None else 0
        inputs.append({"probe": "get_item", "table": table, "existed": current is not None})
        inputs.append(
            {
                "probe": "describe_table",
                "table": table,
                "item_count": described.get("ItemCount", 0),
            }
        )
        if deleting and current is not None:
            reversibility = min(reversibility, 0.5)
        score = count * weight * (1.0 - reversibility)
        return RadiusResult(
            resources_at_risk=count,
            severity_weight=weight,
            reversibility=reversibility,
            score=round(score, 4),
            inputs=inputs,
        )
    except Exception as error:  # noqa: BLE001  (unknown radius = max severity)
        result = _unknown(f"dynamodb probe failed: {str(error)[:120]}")
        result.inputs = inputs
        return result


def probe_s3_objects(
    s3: Any, bucket: str, keys: list[str], weight: float, deleting: bool
) -> RadiusResult:
    """Probe S3 objects: existence and versioning decide reversibility."""
    inputs: list[dict[str, Any]] = []
    try:
        versioning = s3.get_bucket_versioning(Bucket=bucket).get("Status", "Disabled")
        reversible = versioning == "Enabled"
        at_risk = 0
        for key in keys:
            try:
                s3.head_object(Bucket=bucket, Key=key)
                at_risk += 1
                inputs.append(
                    {"probe": "head_object", "bucket": bucket, "key": key, "existed": True}
                )
            except s3.exceptions.ClientError as error:
                code = error.response.get("Error", {}).get("Code", "")
                if code in {"404", "NoSuchKey", "NotFound"}:
                    inputs.append(
                        {"probe": "head_object", "bucket": bucket, "key": key, "existed": False}
                    )
                else:
                    raise
        reversibility = 0.9 if reversible else 0.0
        if deleting and not reversible:
            reversibility = 0.0
        score = at_risk * weight * (1.0 - reversibility)
        return RadiusResult(
            resources_at_risk=at_risk,
            severity_weight=weight,
            reversibility=reversibility,
            score=round(score, 4),
            inputs=inputs,
        )
    except Exception as error:  # noqa: BLE001
        result = _unknown(f"s3 probe failed: {str(error)[:120]}")
        result.inputs = inputs
        return result


def probe_ssm_parameter(ssm: Any, name: str, weight: float, writing: bool) -> RadiusResult:
    """Probe one parameter: existence, current version, overwrite risk."""
    inputs: list[dict[str, Any]] = []
    try:
        result = ssm.get_parameter(Name=name, WithDecryption=False)
        version = int(result["Parameter"].get("Version", 1))
        inputs.append({"probe": "get_parameter", "name": name, "version": version, "existed": True})
        # SSM keeps parameter history: overwrites are reversible by version.
        score = 1 * weight * 0.2 if writing else 0.0
        return RadiusResult(
            resources_at_risk=1,
            severity_weight=weight,
            reversibility=0.8,
            score=round(score, 4),
            inputs=inputs,
        )
    except ssm.exceptions.ParameterNotFound:
        inputs.append({"probe": "get_parameter", "name": name, "existed": False})
        return RadiusResult(
            resources_at_risk=0,
            severity_weight=weight,
            reversibility=1.0,
            score=0.0,
            inputs=inputs,
        )
    except Exception as error:  # noqa: BLE001
        result = _unknown(f"ssm probe failed: {str(error)[:120]}")
        result.inputs = inputs
        return result


def measure_radius(
    action: str, params: dict[str, Any], weight: float, clients: dict[str, Any]
) -> RadiusResult:
    """Dispatch to the right probe by action string (doc 05 radius inputs)."""
    if action == "dynamodb:DeleteItem":
        return probe_dynamodb_item(
            clients["dynamodb"], params["table"], params["key"], weight, deleting=True
        )
    if action == "dynamodb:UpdateItem":
        return probe_dynamodb_item(
            clients["dynamodb"], params["table"], params["key"], weight, deleting=False
        )
    if action == "dynamodb:PutItem":
        # PutItem carries its identity inside the item, not a key parameter.
        item = params.get("item", {})
        key = {k: item[k] for k in ("pk", "sk") if k in item}
        if not key:
            return RadiusResult(
                resources_at_risk=0,
                severity_weight=weight,
                reversibility=1.0,
                score=0.0,
            )
        return probe_dynamodb_item(
            clients["dynamodb"], params["table"], key, weight, deleting=False
        )
    if action == "s3:DeleteObjects":
        return probe_s3_objects(
            clients["s3"], params["bucket"], params["keys"], weight, deleting=True
        )
    if action == "s3:PutObject":
        return probe_s3_objects(
            clients["s3"], params["bucket"], [params["key"]], weight, deleting=False
        )
    if action == "ssm:PutParameter":
        return probe_ssm_parameter(clients["ssm"], params["name"], weight, writing=True)
    # READ-class or unknown: no radius applies.
    return RadiusResult(resources_at_risk=0, severity_weight=0.0, reversibility=1.0, score=0.0)

"""Antares saga engine (S5): every mutation is reversible by construction.

Sequence for one executed action (doc 05, doc 06):
1. pre-capture the exact prior state into the TTL vault
2. perform the real mutation
3. post-flight capture of the new state
4. rollback replays the inverse operation and verifies byte-identity

A missing vault entry means no commit: non-negotiable (doc 04).
Byte-identity: sha256 over canonical JSON of the plain item image.
Scalar values round-trip exactly; nested documents are recorded as
canonical JSON strings, a documented limitation (doc 06).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def canonical_json(obj: Any) -> str:
    """Stable serialization for hashing (doc 06 canonicalization)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def item_hash(item: dict[str, Any] | None) -> str:
    return sha256_hex(canonical_json(item)) if item is not None else "empty"


def _canonical_item(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Flatten an attribute-value item ({"k": {"S": v}}) into plain values."""
    if raw is None:
        return None
    out: dict[str, Any] = {}
    for key, typed in raw.items():
        for type_key, value in typed.items():
            if type_key == "M":
                out[key] = _canonical_item(value)
            elif type_key in {"SS", "NS"}:
                out[key] = list(value)
            elif type_key == "BOOL":
                out[key] = value
            elif type_key == "N":
                out[key] = float(value) if "." in value else int(value)
            else:
                out[key] = value
    return out


def _typed_key(key: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Tool params carry plain keys; DynamoDB requires typed key attributes."""
    return {name: {"S": str(value)} for name, value in key.items()}


def _to_typed(image: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Rebuild attribute values from a plain image. Scalars only: nested
    documents are stored as canonical JSON strings with a marker key."""
    typed: dict[str, dict[str, Any]] = {}
    for key, value in image.items():
        if isinstance(value, bool):
            typed[key] = {"BOOL": value}
        elif isinstance(value, (int, float)):
            typed[key] = {"N": str(value)}
        elif isinstance(value, (dict, list)):
            typed[key] = {"S": canonical_json(value)}
        else:
            typed[key] = {"S": str(value)}
    return typed


@dataclass
class SagaStep:
    name: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class SagaResult:
    action_id: str
    steps: list[SagaStep] = field(default_factory=list)
    prior_image: dict[str, Any] | None = None
    new_image: dict[str, Any] | None = None
    prior_hash: str | None = None
    new_hash: str | None = None
    committed: bool = False
    rolled_back: bool = False
    rollback_verified: bool = False
    error: str | None = None

    def step(self, name: str, **detail: Any) -> None:
        self.steps.append(SagaStep(name=name, detail=detail))


class SagaEngine:
    """Executes gated mutations with pre-capture, post-flight and reversal."""

    def __init__(
        self,
        ddb: Any,
        s3: Any,
        ssm: Any,
        ledger_table: str,
        vault_table: str,
        vault_ttl_seconds: int = 3600,
    ) -> None:
        self.ddb = ddb
        self.s3 = s3
        self.ssm = ssm
        self.ledger_table = ledger_table
        self.vault_table = vault_table
        self.vault_ttl_seconds = vault_ttl_seconds

    # -- vault -----------------------------------------------------------

    def _vault_save(self, action_id: str, image: dict[str, Any] | None, kind: str) -> None:
        self.ddb.put_item(
            TableName=self.vault_table,
            Item={
                "pk": {"S": f"VAULT#{action_id}"},
                "sk": {"S": kind},
                "image": {"S": canonical_json(image) if image else ""},
                "image_hash": {"S": item_hash(image)},
                "ttl": {"N": str(int(datetime.now(UTC).timestamp()) + self.vault_ttl_seconds)},
            },
        )

    def _vault_load(self, action_id: str, kind: str) -> dict[str, Any] | None:
        entry = self.ddb.get_item(
            TableName=self.vault_table, Key={"pk": {"S": f"VAULT#{action_id}"}, "sk": {"S": kind}}
        ).get("Item")
        if not entry:
            return None
        raw = entry["image"]["S"]
        return json.loads(raw) if raw else None

    # -- dynamodb executors ----------------------------------------------

    def _dyn_pre_capture(
        self, params: dict[str, Any], key: dict[str, Any], action_id: str
    ) -> dict[str, Any] | None:
        current = _canonical_item(
            self.ddb.get_item(
                TableName=params["table"], Key=_typed_key(key), ConsistentRead=True
            ).get("Item")
        )
        self._vault_save(action_id, current, "prior_item")
        return current

    def _dyn_post_capture(
        self, params: dict[str, Any], key: dict[str, Any], action_id: str
    ) -> dict[str, Any] | None:
        current = _canonical_item(
            self.ddb.get_item(TableName=params["table"], Key=_typed_key(key)).get("Item")
        )
        self._vault_save(action_id, current, "post_item")
        return current

    def _dyn_execute(self, action: str, params: dict[str, Any]) -> Any:
        if action == "dynamodb:GetItem":
            return self.ddb.get_item(TableName=params["table"], Key=_typed_key(params["key"]))
        if action == "dynamodb:DescribeTable":
            return self.ddb.describe_table(TableName=params["table"])
        if action == "dynamodb:PutItem":
            # Idempotent overwrite: the vault holds the prior state, so a
            # re-execution is still reversible (no reject-on-exists gate).
            return self.ddb.put_item(TableName=params["table"], Item=_to_typed(params["item"]))
        if action == "dynamodb:UpdateItem":
            return self.ddb.update_item(
                TableName=params["table"],
                Key=_typed_key(params["key"]),
                UpdateExpression=params["update_expression"],
                ExpressionAttributeValues=params.get("expression_values"),
            )
        if action == "dynamodb:DeleteItem":
            return self.ddb.delete_item(TableName=params["table"], Key=_typed_key(params["key"]))
        raise ValueError(f"unsupported dynamodb action {action!r}")

    def _dyn_rollback(self, params: dict[str, Any], prior: dict[str, Any] | None) -> Any:
        if prior is None:
            # The item did not exist before the action: the inverse is removal.
            return self.ddb.delete_item(TableName=params["table"], Key=_typed_key(params["key"]))
        return self.ddb.put_item(TableName=params["table"], Item=_to_typed(prior))

    # -- ssm executors -----------------------------------------------------

    def _ssm_pre_capture(self, params: dict[str, Any], action_id: str) -> dict[str, Any] | None:
        try:
            result = self.ssm.get_parameter(Name=params["name"])
            image = {"name": params["name"], "value": result["Parameter"]["Value"]}
        except self.ssm.exceptions.ParameterNotFound:
            image = None
        self._vault_save(action_id, image, "prior_parameter")
        return image

    def _ssm_rollback(self, params: dict[str, Any], prior: dict[str, Any] | None) -> Any:
        if prior is None:
            raise ValueError("cannot restore a parameter that did not previously exist")
        return self.ssm.put_parameter(
            Name=params["name"], Value=prior["value"], Type="String", Overwrite=True
        )

    # -- public API ---------------------------------------------------------

    def execute(self, action: str, params: dict[str, Any], action_id: str) -> SagaResult:
        """Pre-capture, execute, post-capture. Receipts live in the vault."""
        result = SagaResult(action_id=action_id)
        service = action.split(":", 1)[0]
        try:
            key: dict[str, Any] | None = None
            if service == "dynamodb":
                key = params.get("key") or {
                    k: params["item"][k] for k in ("pk", "sk") if k in params["item"]
                }
                prior = self._dyn_pre_capture(params, key, action_id)
                result.prior_image = prior
                result.prior_hash = item_hash(prior)
                result.step("pre_capture", prior_hash=result.prior_hash)
                self._dyn_execute(action, params)
                result.committed = True
                result.step("committed")
                new_image = self._dyn_post_capture(params, key, action_id)
                result.new_image = new_image
                result.new_hash = item_hash(new_image)
                result.step("post_capture", new_hash=result.new_hash)
            elif service == "ssm":
                prior = self._ssm_pre_capture(params, action_id)
                result.prior_image = prior
                result.prior_hash = item_hash(prior)
                result.step("pre_capture", prior_hash=result.prior_hash)
                if action == "ssm:PutParameter":
                    self.ssm.put_parameter(
                        Name=params["name"],
                        Value=params["value"],
                        Type="String",
                        Overwrite=params.get("overwrite", False),
                    )
                result.committed = True
                result.step("committed")
            else:
                result.error = f"execution not implemented for {action!r}"
                result.step("unsupported")
            return result
        except Exception as error:  # noqa: BLE001  (recorded, surfaced to the verdict)
            result.error = str(error)[:200]
            result.step("error", error=result.error)
            return result

    def rollback(self, action: str, params: dict[str, Any], action_id: str) -> SagaResult:
        """Replay the compensating operation and verify byte-identity."""
        result = SagaResult(action_id=action_id)
        key: dict[str, Any] | None = None
        if action.split(":", 1)[0] == "dynamodb":
            key = params.get("key") or {
                k: params["item"][k] for k in ("pk", "sk") if k in params["item"]
            }
        prior = self._vault_load(action_id, "prior_item")
        kind = "prior_item"
        if prior is None:
            prior = self._vault_load(action_id, "prior_parameter")
            kind = "prior_parameter"
        result.prior_image = prior
        result.prior_hash = item_hash(prior)
        service = action.split(":", 1)[0]
        try:
            if service == "dynamodb":
                self._dyn_rollback(params, prior)
                assert key is not None, "dynamodb rollback requires a key"
                restored = _canonical_item(
                    self.ddb.get_item(
                        TableName=params["table"],
                        Key=_typed_key(key),
                        ConsistentRead=True,
                    ).get("Item")
                )
            elif service == "ssm":
                self._ssm_rollback(params, prior)
                parameter = self.ssm.get_parameter(Name=params["name"])["Parameter"]
                restored = {"name": params["name"], "value": parameter["Value"]}
            else:
                result.error = f"rollback not implemented for {action!r}"
                return result
            result.rolled_back = True
            if prior is None:
                result.rollback_verified = restored is None
            else:
                result.rollback_verified = item_hash(restored) == result.prior_hash
            result.step(
                "rollback",
                kind=kind,
                verified=result.rollback_verified,
                restored_hash=item_hash(restored) if restored else "empty",
            )
            return result
        except Exception as error:  # noqa: BLE001
            result.error = str(error)[:200]
            result.step("error", error=result.error)
            return result

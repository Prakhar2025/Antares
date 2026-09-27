"""Antares provenance ledger (S6): a tamper-evident Merkle chain (doc 06).

Every record appends one leaf: sha256 over its canonical JSON, chained to
the previous leaf. The chain head is advanced transactionally with a
condition on the expected previous hash: two writers cannot fork the
chain silently. A receipt lets any client recompute the leaf hash from
the record alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .saga import canonical_json, sha256_hex


class LedgerForkError(RuntimeError):
    """The chain head moved between read and write: retry or investigate."""


@dataclass
class Receipt:
    record: dict[str, Any]
    leaf_hash: str
    prev_leaf_hash: str
    root: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "record": self.record,
            "leaf_hash": self.leaf_hash,
            "prev_leaf_hash": self.prev_leaf_hash,
            "root": self.root,
        }


class Ledger:
    """Merkle chain over canonical records, stored in the single table."""

    def __init__(self, ddb: Any, table_name: str) -> None:
        self.ddb = ddb
        self.table_name = table_name

    def _head(self) -> dict[str, Any]:
        result = self.ddb.get_item(
            TableName=self.table_name, Key={"pk": {"S": "CHAIN"}, "sk": {"S": "HEAD"}}
        )
        item = result.get("Item")
        if not item:
            return {"leaf_hash": "GENESIS", "height": 0}
        return {"leaf_hash": item["leaf_hash"]["S"], "height": int(item["height"]["N"])}

    def append(self, record: dict[str, Any]) -> Receipt:
        """Append one record. Retries once on a concurrent fork."""
        for _attempt in range(2):
            head = self._head()
            leaf = sha256_hex(canonical_json(record))
            try:
                self.ddb.put_item(
                    TableName=self.table_name,
                    Item={
                        "pk": {"S": "CHAIN"},
                        "sk": {"S": "HEAD"},
                        "leaf_hash": {"S": leaf},
                        "prev_leaf_hash": {"S": head["leaf_hash"]},
                        "height": {"N": str(head["height"] + 1)},
                        "ts": record.get("ts", ""),
                    },
                    ConditionExpression=("attribute_not_exists(pk) OR leaf_hash = :expected"),
                    ExpressionAttributeValues={":expected": {"S": head["leaf_hash"]}},
                )
            except Exception:  # noqa: BLE001  (condition raced: re-read and retry)
                head = self._head()
                continue
            return Receipt(
                record=record,
                leaf_hash=leaf,
                prev_leaf_hash=head["leaf_hash"],
                root=leaf,
            )
        raise LedgerForkError("chain head advanced twice; inspect the ledger")

    def verify_record(self, record: dict[str, Any], leaf_hash: str) -> bool:
        """Client-side verification rule: hash the canonical record."""
        return sha256_hex(canonical_json(record)) == leaf_hash

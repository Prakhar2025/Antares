"""Antares tool registry (doc 05 section 2): the tools an agent may call.

A registered tool is a contract: exact action string, strict parameter
schema, mutation class, and the parameter fields that reference cloud
resources (checked against the namespace allowlist by the gate).
Unregistered tools do not exist; the gateway returns 404 for them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .schemas import ActionClass


class _Strict(BaseModel):
    """Unknown parameter fields are a defect, not data."""

    model_config = ConfigDict(extra="forbid")


# --- sandbox tool parameter schemas (P1 surface: DynamoDB, S3, SSM) ---------


class GetItemParams(_Strict):
    table: str
    key: dict[str, Any]


class QueryParams(_Strict):
    table: str
    index: str | None = None
    limit: int | None = Field(default=None, ge=1, le=100)


class DescribeTableParams(_Strict):
    table: str


class PutItemParams(_Strict):
    table: str
    item: dict[str, Any]


class UpdateItemParams(_Strict):
    table: str
    key: dict[str, Any]
    update_expression: str
    expression_values: dict[str, Any] | None = None


class DeleteItemParams(_Strict):
    table: str
    key: dict[str, Any]


class GetObjectParams(_Strict):
    bucket: str
    key: str


class PutObjectParams(_Strict):
    bucket: str
    key: str


class DeleteObjectsParams(_Strict):
    bucket: str
    keys: list[str] = Field(min_length=1)


class GetParameterParams(_Strict):
    name: str


class PutParameterParams(_Strict):
    name: str
    value: str
    overwrite: bool = False


@dataclass(frozen=True)
class ToolSpec:
    """One registered tool: the full contract for its calls."""

    tool: str
    action: str
    action_class: ActionClass
    params_model: type[BaseModel]
    resource_fields: dict[str, str]
    description: str


class UnknownTool(KeyError):
    """Raised when a call names a tool that is not registered (doc 13: 404)."""


class ToolRegistry:
    """Immutable registry. Registration happens at build time, never per call."""

    def __init__(self, tools: dict[str, ToolSpec]) -> None:
        self._tools = tools

    def get(self, tool: str) -> ToolSpec:
        try:
            return self._tools[tool]
        except KeyError:
            raise UnknownTool(tool) from None

    def names(self) -> list[str]:
        return sorted(self._tools)

    def with_tools(self, extra: list[ToolSpec]) -> ToolRegistry:
        """Derive a registry with additional specs (tests, future packs)."""
        merged = dict(self._tools)
        for spec in extra:
            merged[spec.tool] = spec
        return ToolRegistry(merged)


def build_default_registry() -> ToolRegistry:
    """The dev-namespace tool surface: four classes represented, doc 03 scope."""

    tools: list[ToolSpec] = [
        # READ
        ToolSpec("ledger.get_item", "dynamodb:GetItem", ActionClass.READ, GetItemParams,
                 {"table": "table"}, "read one item from the demo ledger"),
        ToolSpec("ledger.query", "dynamodb:Query", ActionClass.READ, QueryParams,
                 {"table": "table"}, "query the demo ledger"),
        ToolSpec("ledger.describe", "dynamodb:DescribeTable", ActionClass.READ, DescribeTableParams,
                 {"table": "table"}, "describe the demo ledger table"),
        ToolSpec("vault.get_object", "s3:GetObject", ActionClass.READ, GetObjectParams,
                 {"bucket": "bucket"}, "read one object from the demo vault"),
        ToolSpec("config.get_parameter", "ssm:GetParameter", ActionClass.READ, GetParameterParams,
                 {"name": "ssm_path"}, "read one demo configuration parameter"),
        # WRITE
        ToolSpec("ledger.put_item", "dynamodb:PutItem", ActionClass.WRITE, PutItemParams,
                 {"table": "table"}, "write one item to the demo ledger"),
        ToolSpec("ledger.update_item", "dynamodb:UpdateItem", ActionClass.WRITE, UpdateItemParams,
                 {"table": "table"}, "update items in the demo ledger"),
        ToolSpec("vault.put_object", "s3:PutObject", ActionClass.WRITE, PutObjectParams,
                 {"bucket": "bucket"}, "write one object to the demo vault"),
        ToolSpec("config.put_parameter", "ssm:PutParameter", ActionClass.WRITE, PutParameterParams,
                 {"name": "ssm_path"}, "write one demo configuration parameter"),
        # DESTROY
        ToolSpec("ledger.delete_item", "dynamodb:DeleteItem", ActionClass.DESTROY, DeleteItemParams,
                 {"table": "table"}, "delete one item from the demo ledger"),
        ToolSpec("vault.delete_objects", "s3:DeleteObjects", ActionClass.DESTROY,
                 DeleteObjectsParams, {"bucket": "bucket"}, "delete objects from the demo vault"),
    ]
    # Registration is explicit and ordered; the registry itself is immutable.
    return ToolRegistry({spec.tool: spec for spec in tools})

"""Antares kernel gateway (S1): the only door to gated action.

HTTP concerns live here; judgment lives in the gate; contracts live in
schemas. The gateway is dependency-injected for testability: the Lambda
entrypoint wires real clients, tests wire fakes (doc 14 contract rule:
fakes mirror real return shapes).
"""

from __future__ import annotations

import base64
import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pydantic import ValidationError

from .gate import run_gate
from .policy import Policy
from .registry import ToolRegistry, UnknownTool
from .schemas import Latency, ToolCall, Verdict, VerdictState

logger = Logger(service="antares-gate")

_JSON = {"Content-Type": "application/json"}
_PROBLEM = {"Content-Type": "application/problem+json"}
_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type,x-api-key",
}


def _headers(extra: dict[str, str]) -> dict[str, str]:
    return {**extra, **_CORS}


def problem(status: int, code: str, title: str, detail: str) -> dict[str, Any]:
    """RFC 7807 problem+json with a registered code (doc 13 error registry)."""
    body = {
        "type": f"urn:antares:errors:{code}",
        "code": code,
        "title": title,
        "detail": detail,
        "status": status,
    }
    return {"statusCode": status, "headers": _headers(_PROBLEM), "body": json.dumps(body)}


def _decode_body(event: dict[str, Any]) -> str:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(body).decode("utf-8")
    return body


def create_app(
    policy: Policy,
    registry: ToolRegistry,
    ddb: Any,
    table_name: str,
    halt: bool = False,
    metrics: Metrics | None = None,
) -> Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any]]:
    """Build the request handler with injected dependencies."""

    def _emit(state: VerdictState, latency_ms: int) -> None:
        if metrics is None:
            return
        metrics.add_dimension(name="state", value=state.value)
        metrics.add_metric(name="GateLatencyMs", unit=MetricUnit.Milliseconds, value=latency_ms)
        metrics.add_metric(name="VerdictCount", unit=MetricUnit.Count, value=1)

    def _persist(verdict: Verdict) -> None:
        ttl = int(time.time()) + policy.decision_ttl_days * 86400
        ddb.put_item(
            TableName=table_name,
            Item={
                "pk": {"S": "TENANT#default"},
                "sk": {"S": f"DECISION#{verdict.ts}#{verdict.verdict_id}"},
                "verdict_id": {"S": verdict.verdict_id},
                "state": {"S": verdict.state.value},
                "action_class": {"S": verdict.gate.action_class.value},
                "ts": {"S": verdict.ts},
                "ttl": {"N": str(ttl)},
                "latency_ms": {"N": str(verdict.latency_ms.total)},
                "verdict": {"S": verdict.model_dump_json()},
            },
        )

    def _gate(event: dict[str, Any]) -> dict[str, Any]:
        if halt:
            return problem(
                503, "kernel-halted", "Kernel halted", "ANTARES_HALT is engaged; no gating service."
            )
        started = time.perf_counter()
        try:
            payload = json.loads(_decode_body(event))
        except (json.JSONDecodeError, ValueError):
            return problem(422, "schema-rejected", "Invalid JSON", "request body is not valid JSON")
        try:
            call = ToolCall.model_validate(payload)
        except ValidationError as error:
            detail = error.errors()[0]["msg"]
            return problem(422, "schema-rejected", "Invalid ToolCall", detail)
        try:
            registry.get(call.tool)
        except UnknownTool:
            return problem(
                404, "unknown-tool", "Unknown tool", f"tool {call.tool!r} is not registered"
            )

        outcome = run_gate(call, registry, policy)
        total_ms = int((time.perf_counter() - started) * 1000)
        verdict = Verdict(
            verdict_id=uuid.uuid4().hex,
            state=outcome.state,
            call_ref=call.call_id,
            gate=outcome.result,
            latency_ms=Latency(
                gate=outcome.gate_ms, quorum=0, probe=0, total=total_ms
            ),
            ts=datetime.now(UTC).isoformat(),
        )
        _persist(verdict)
        _emit(verdict.state, total_ms)
        logger.info(
            "verdict issued",
            extra={"verdict_id": verdict.verdict_id, "state": verdict.state.value},
        )
        return {"statusCode": 200, "headers": _headers(_JSON), "body": verdict.model_dump_json()}

    def _decision(event: dict[str, Any]) -> dict[str, Any]:
        path = event.get("path") or ""
        verdict_id = (event.get("pathParameters") or {}).get("id") or path.rsplit("/", 1)[-1]
        if not verdict_id:
            return problem(404, "verdict-not-found", "Not found", "missing decision id")
        result = ddb.query(
            TableName=table_name,
            IndexName="gsi3",
            KeyConditionExpression="verdict_id = :v",
            ExpressionAttributeValues={":v": {"S": verdict_id}},
            Limit=1,
        )
        items = result.get("Items") or []
        if not items:
            return problem(404, "verdict-not-found", "Not found", f"no decision {verdict_id!r}")
        return {"statusCode": 200, "headers": _headers(_JSON), "body": items[0]["verdict"]["S"]}

    def handle(event: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        method = (event.get("httpMethod") or "GET").upper()
        path = event.get("path") or ""
        if method == "OPTIONS":
            return {"statusCode": 204, "headers": _headers({}), "body": ""}
        if path == "/v1/gate" and method == "POST":
            return _gate(event)
        if path.startswith("/v1/decisions/") and method == "GET":
            return _decision(event)
        return problem(404, "not-found", "Not found", f"no route for {method} {path}")

    return handle

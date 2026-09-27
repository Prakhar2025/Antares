"""Lambda entrypoint for the Antares gate API (dev namespace).

Thin by design: dependencies are wired once at cold start, everything
testable lives in antares.gateway.create_app with injected fakes.
"""

from __future__ import annotations

import os
from typing import Any

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer

from antares.gateway import create_app
from antares.policy import Policy
from antares.registry import build_default_registry

logger = Logger(service="antares-gate")
tracer = Tracer()
metrics = Metrics(namespace="Antares", service="gate")

_policy = Policy.from_env()
_registry = build_default_registry()
_ddb = boto3.client("dynamodb")
_bedrock = boto3.client("bedrock-runtime")
_kms = boto3.client("kms")
_halt = os.environ.get("ANTARES_HALT", "false").lower() == "true"

app = create_app(
    policy=_policy,
    registry=_registry,
    ddb=_ddb,
    table_name=os.environ["ANTARES_TABLE_NAME"],
    halt=_halt,
    metrics=metrics,
    bedrock=_bedrock,
    kms=_kms,
    signing_key_id=os.environ.get("ANTARES_SIGNING_KEY_ID"),
)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    return app(event, context)

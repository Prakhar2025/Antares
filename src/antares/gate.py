"""Antares deterministic gate (S2, ADR-001): pure code with veto power.

No model is ever consulted here. The gate runs in microseconds, produces
named findings, and holds veto: any block-severity finding ends the call
before the quorum layer is even considered. Fusion for P1:

- any block finding                      -> HARD_BLOCK (ADR-001 veto)
- class denied by namespace policy       -> HARD_BLOCK (doc 05 rule 5)
- class in escalate set, clean otherwise -> ABSTAIN (doc 05 rule 2; the
  quorum that reviews ABSTAIN ships in pipeline v2, doc 11 P2)
- otherwise                              -> ALLOW
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from .policy import Policy
from .registry import ToolRegistry
from .schemas import Finding, GateResult, ToolCall, VerdictState

META_CHARS: tuple[str, ...] = ("&&", "||", "`", "$(", ";", "|")
DESTRUCTIVE_PATTERNS: tuple[str, ...] = (
    "rm -rf",
    "mkfs",
    "dd if=",
    "shutdown",
    ":(){",
    "del /",
    "> /dev/",
)


@dataclass(frozen=True)
class GateOutcome:
    """The gate's complete output: state, named findings, microseconds."""

    state: VerdictState
    result: GateResult
    gate_ms: int


def _iter_strings(value: Any, prefix: str = "params") -> Iterator[tuple[str, str]]:
    """Yield (path, text) for every string leaf inside the params object."""
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{prefix}[{index}]")


def _resource_finding(field: str, kind: str, value: str, policy: Policy) -> Finding | None:
    """Check one resource-referencing parameter against the namespace allowlist."""
    if kind == "table" and value not in policy.allowed_tables:
        return Finding(
            rule_id="GATE-ARN-001",
            detail=f"table {value!r} is outside the namespace allowlist",
            severity="block",
        )
    if kind == "bucket" and value not in policy.allowed_buckets:
        return Finding(
            rule_id="GATE-ARN-001",
            detail=f"bucket {value!r} is outside the namespace allowlist",
            severity="block",
        )
    if kind == "ssm_path" and not value.startswith(policy.allowed_ssm_prefix):
        return Finding(
            rule_id="GATE-ARN-001",
            detail=(
                f"parameter path {value!r} is outside the namespace prefix "
                f"{policy.allowed_ssm_prefix!r}"
            ),
            severity="block",
        )
    return None


def _first_schema_error(error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(part) for part in first["loc"]) or "params"
    return f"{location}: {first['msg']}"


def run_gate(call: ToolCall, registry: ToolRegistry, policy: Policy) -> GateOutcome:
    """Evaluate one resolved call against schema, namespace and policy.

    The caller must have resolved the tool (UnknownTool is the gateway's
    404, not a gate finding). Pure function over its inputs.
    """
    started = time.perf_counter()
    spec = registry.get(call.tool)
    findings: list[Finding] = []

    if call.action != spec.action:
        findings.append(
            Finding(
                rule_id="GATE-ACT-001",
                detail=f"action {call.action!r} does not match registered action {spec.action!r}",
                severity="block",
            )
        )

    try:
        spec.params_model.model_validate(call.params)
    except ValidationError as error:
        findings.append(
            Finding(
                rule_id="GATE-SCH-001",
                detail=f"parameters failed the tool schema: {_first_schema_error(error)}",
                severity="block",
            )
        )

    for field, kind in spec.resource_fields.items():
        value = call.params.get(field)
        if isinstance(value, str):
            finding = _resource_finding(field, kind, value, policy)
            if finding is not None:
                findings.append(finding)

    for path, text in _iter_strings(call.params):
        for metachar in META_CHARS:
            if metachar in text:
                findings.append(
                    Finding(
                        rule_id="GATE-SHL-001",
                        detail=f"shell metacharacter {metachar!r} in {path}",
                        severity="block",
                    )
                )
                break
        lowered = text.lower()
        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern in lowered:
                findings.append(
                    Finding(
                        rule_id="GATE-SHL-002",
                        detail=f"destructive pattern {pattern!r} in {path}",
                        severity="block",
                    )
                )
                break

    weight = policy.class_weights[spec.action_class.value]
    findings.append(
        Finding(
            rule_id="GATE-CLS-001",
            detail=f"action class {spec.action_class.value} carries severity weight {weight}",
            severity="info",
        )
    )

    code_blocked = any(finding.severity == "block" for finding in findings)
    if spec.action_class.value in policy.deny_classes:
        findings.append(
            Finding(
                rule_id="GATE-POL-001",
                detail=f"action class {spec.action_class.value} is denied by namespace policy",
                severity="block",
            )
        )
        code_blocked = True

    if code_blocked:
        state = VerdictState.HARD_BLOCK
    elif spec.action_class.value in policy.escalate_classes:
        state = VerdictState.ABSTAIN
        findings.append(
            Finding(
                rule_id="GATE-ESC-001",
                detail="action class requires quorum review; the quorum ships in pipeline v2",
                severity="info",
            )
        )
    else:
        state = VerdictState.ALLOW

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = GateResult(
        code_blocked=code_blocked, action_class=spec.action_class, findings=findings
    )
    return GateOutcome(state=state, result=result, gate_ms=elapsed_ms)

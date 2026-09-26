"""Antares contracts (doc 05): the schemas every call and verdict must satisfy.

These are the law. Where code and doc disagree, one of them is a defect.
Pydantic v2, strict by default: unknown fields are rejected, not absorbed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ActionClass(StrEnum):
    """Mutation severity classes (doc 05 section 2, weights in doc 06)."""

    READ = "READ"
    WRITE = "WRITE"
    PERMISSION = "PERMISSION"
    DESTROY = "DESTROY"


class VerdictState(StrEnum):
    """Three-state verdict (doc 05 section 4). Never an average."""

    ALLOW = "ALLOW"
    HARD_BLOCK = "HARD_BLOCK"
    ABSTAIN = "ABSTAIN"


class _Strict(BaseModel):
    """Base for all wire models: unknown fields are a defect, not data."""

    model_config = ConfigDict(extra="forbid")


class Session(_Strict):
    """Per-agent-session context carried on every call (doc 05 section 2)."""

    session_id: str = Field(min_length=8)
    trust_score: float = Field(default=0.0, ge=0.0, le=1.0)
    perimeter: list[str] = Field(default_factory=list)


class ToolCall(_Strict):
    """The only shape the gateway accepts (doc 05 section 2)."""

    call_id: str = Field(min_length=4)
    tool: str = Field(min_length=3)
    action: str = Field(min_length=3)
    params: dict[str, Any]
    session: Session
    requested_by: str = Field(min_length=1)


class Finding(_Strict):
    """One named gate rule that fired. An unnamed rule firing is a defect."""

    rule_id: str
    detail: str
    severity: Literal["info", "flag", "block"] = "info"


class GateResult(_Strict):
    """Deterministic gate section of a verdict (doc 05 section 3)."""

    code_blocked: bool
    action_class: ActionClass
    findings: list[Finding] = Field(default_factory=list)


class Latency(_Strict):
    """Latency breakdown in milliseconds (doc 05 section 3, budgets doc 17)."""

    gate: int = 0
    quorum: int = 0
    probe: int = 0
    total: int = 0


class Verdict(_Strict):
    """The kernel's decision (doc 05 section 3). P1 fills gate and latency;
    quorum, radius, bypass and merkle_root are typed placeholders that P2
    and P3 populate. The shape is versioned so consumers can pin."""

    schema_version: Literal["v1"] = "v1"
    verdict_id: str
    state: VerdictState
    call_ref: str
    gate: GateResult
    diagnosis: str | None = None
    quorum: dict[str, Any] | None = None
    radius: dict[str, Any] | None = None
    bypass: dict[str, Any] | None = None
    merkle_root: str | None = None
    latency_ms: Latency = Field(default_factory=Latency)
    ts: str

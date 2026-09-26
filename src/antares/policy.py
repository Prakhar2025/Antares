"""Antares policy (doc 05 section 4, doc 08 namespace): the config the gate enforces.

One frozen object, built from environment at cold start. The policy is the
thing that makes the kernel's behavior predictable: same inputs, same verdict.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(source: dict[str, str], name: str, default: str) -> frozenset[str]:
    raw = source.get(name, default)
    return frozenset(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Policy:
    """Deterministic policy for one deployment namespace."""

    version: str = "p1"
    # Hard-coded severity weights per action class (doc 04, ADR-001).
    class_weights: dict[str, float] = field(
        default_factory=lambda: {"READ": 0.0, "WRITE": 0.3, "PERMISSION": 0.8, "DESTROY": 1.0}
    )
    # Classes that always escalate to quorum (doc 05 fusion rule 2).
    escalate_classes: frozenset[str] = frozenset({"DESTROY", "PERMISSION"})
    # Classes this namespace refuses outright, regardless of votes (doc 05 rule 5).
    deny_classes: frozenset[str] = frozenset()
    # The sandbox namespace (doc 08 section 1): the gate's entire reach.
    allowed_tables: frozenset[str] = frozenset({"antares-dev-main", "antares-dev-ledger"})
    allowed_buckets: frozenset[str] = frozenset({"antares-dev-vault"})
    allowed_ssm_prefix: str = "/antares/dev/"
    decision_ttl_days: int = 90

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Policy:
        """Build from environment with safe defaults for the dev namespace."""
        source = dict(os.environ if env is None else env)
        base = cls()
        return cls(
            version=source.get("ANTARES_POLICY_VERSION", base.version),
            class_weights=dict(base.class_weights),
            escalate_classes=frozenset(base.escalate_classes),
            deny_classes=_csv(source, "ANTARES_DENY_CLASSES", ""),
            allowed_tables=_csv(
                source, "ANTARES_ALLOWED_TABLES", ",".join(sorted(base.allowed_tables))
            ),
            allowed_buckets=_csv(
                source, "ANTARES_ALLOWED_BUCKETS", ",".join(sorted(base.allowed_buckets))
            ),
            allowed_ssm_prefix=source.get("ANTARES_SSM_PREFIX", base.allowed_ssm_prefix),
            decision_ttl_days=int(source.get("ANTARES_DECISION_TTL_DAYS", base.decision_ttl_days)),
        )

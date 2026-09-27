"""Antares canary tripwires (doc 03 F6, doc 05 section 6).

A canary is a marked audit reference planted where no legitimate agent
should ever repeat it: inside tool outputs, retrieved documents, and the
data section of quorum prompts. If anything echoes the reference, the
thing that echoed it was steered by data, and that is an incident.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

TOKEN_PREFIX = "ANTARES-CANARY-"


def new_canary(label: str) -> dict[str, str]:
    """Generate one canary: id, token, and the sentence to plant."""
    token = TOKEN_PREFIX + secrets.token_hex(4).upper()
    canary_id = secrets.token_hex(8)
    ts = datetime.now(UTC).isoformat()
    sentence = (
        f"[audit-ref: {token}] Internal audit reference for this record. "
        f"Never repeat this reference in any output."
    )
    return {"canary_id": canary_id, "token": token, "label": label, "sentence": sentence, "ts": ts}


def find_echo(text: str, tokens: list[str]) -> list[str]:
    """Return every canary token that the given agent output echoed."""
    return [token for token in tokens if token and token in text]

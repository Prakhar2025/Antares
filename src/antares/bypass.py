"""Antares bypass tokens (doc 05 section 5, ADR-005).

An ABSTAIN verdict suspends an action and issues one token: KMS-signed,
bound to the verdict and call ids, single-use, dead in 60 seconds. The
raw token exists only in the API response; the kernel stores its hash.
Redemption is a conditional transaction: two racers, one winner.
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

TOKEN_PREFIX = "v1."


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_bypass(
    kms: Any,
    key_id: str,
    verdict_id: str,
    call_id: str,
    ttl_seconds: int = 60,
) -> dict[str, Any]:
    """Sign one bypass token with KMS HMAC and return its response shape."""
    now = int(datetime.now(UTC).timestamp())
    payload = json.dumps(
        {"v": verdict_id, "c": call_id, "exp": now + ttl_seconds},
        separators=(",", ":"),
    )
    payload_b64 = _b64url(payload.encode())
    mac = kms.generate_mac(
        KeyId=key_id,
        MessageId="antares-bypass",
        Message=payload_b64.encode(),
        MacAlgorithm="HMAC_SHA_256",
    )["Mac"]
    token = f"{TOKEN_PREFIX}{payload_b64}.{_b64url(mac)}"
    return {
        "token": token,
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "expires_at": now + ttl_seconds,
        "single_use": True,
    }


def verify_bypass(
    kms: Any,
    key_id: str,
    token: str,
    verdict_id: str,
    now: int | None = None,
) -> tuple[bool, str]:
    """Verify signature, expiry and verdict binding. Returns (ok, reason)."""
    if not token.startswith(TOKEN_PREFIX):
        return False, "token format not recognized"
    try:
        payload_b64, mac_b64 = token[len(TOKEN_PREFIX) :].split(".", 1)
    except ValueError:
        return False, "token malformed"
    current = int(datetime.now(UTC).timestamp()) if now is None else now
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))
    except (ValueError, json.JSONDecodeError):
        return False, "token payload unreadable"
    if payload.get("v") != verdict_id:
        return False, "token is bound to a different verdict"
    if int(payload.get("exp", 0)) < current:
        return False, "token expired"
    try:
        mac = base64.urlsafe_b64decode(mac_b64 + "=" * (-len(mac_b64) % 4))
        result = kms.verify_mac(
            KeyId=key_id,
            MessageId="antares-bypass",
            Message=payload_b64.encode(),
            MacAlgorithm="HMAC_SHA_256",
            Mac=mac,
        )
    except Exception:  # noqa: BLE001  (KMS raises on invalid MAC shape)
        return False, "token signature invalid"
    if not result.get("MacValid"):
        return False, "token signature invalid"
    return True, "ok"

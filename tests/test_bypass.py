"""Bypass token tests: HMAC signing, expiry, binding, tamper rejection."""

import hashlib
import hmac as hmac_lib

from antares.bypass import issue_bypass, verify_bypass


class FakeKms:
    """Mirrors KMS GenerateMac and VerifyMac semantics."""

    def __init__(self, key: bytes = b"antares-test-signing-key") -> None:
        self.key = key
        self.generations = 0

    def generate_mac(self, KeyId: str, MessageId: str, Message: bytes, MacAlgorithm: str) -> dict:  # noqa: N803
        self.generations += 1
        return {"Mac": hmac_lib.new(self.key, Message, hashlib.sha256).digest()}

    def verify_mac(
        self, KeyId: str, MessageId: str, Message: bytes, MacAlgorithm: str, Mac: bytes
    ) -> dict:  # noqa: N803
        expected = hmac_lib.new(self.key, Message, hashlib.sha256).digest()
        return {"MacValid": hmac_lib.compare_digest(expected, Mac)}


class TestIssueAndVerify:
    def test_happy_path(self) -> None:
        kms = FakeKms()
        issued = issue_bypass(kms, "key", "verdict-1", "call-1", ttl_seconds=60)
        ok, reason = verify_bypass(
            kms, "key", issued["token"], "verdict-1", now=issued["expires_at"] - 1
        )
        assert ok is True
        assert reason == "ok"

    def test_single_use_shape(self) -> None:
        issued = issue_bypass(FakeKms(), "key", "verdict-1", "call-1")
        assert issued["single_use"] is True
        assert len(issued["token_hash"]) == 64

    def test_expired_token_rejected(self) -> None:
        kms = FakeKms()
        issued = issue_bypass(kms, "key", "verdict-1", "call-1", ttl_seconds=60)
        ok, reason = verify_bypass(
            kms, "key", issued["token"], "verdict-1", now=issued["expires_at"] + 1
        )
        assert ok is False
        assert reason == "token expired"

    def test_wrong_verdict_rejected(self) -> None:
        kms = FakeKms()
        issued = issue_bypass(kms, "key", "verdict-1", "call-1")
        ok, reason = verify_bypass(kms, "key", issued["token"], "verdict-2")
        assert ok is False
        assert reason == "token is bound to a different verdict"

    def test_tampered_payload_rejected(self) -> None:
        kms = FakeKms()
        issued = issue_bypass(kms, "key", "verdict-1", "call-1")
        token = issued["token"][:-4] + "AAAA"
        ok, reason = verify_bypass(kms, "key", token, "verdict-1")
        assert ok is False
        assert reason == "token signature invalid"

    def test_garbage_rejected(self) -> None:
        ok, _reason = verify_bypass(FakeKms(), "key", "not-a-token", "verdict-1")
        assert ok is False

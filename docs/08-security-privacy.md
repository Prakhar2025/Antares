# Doc 08: Security and Privacy

Version 0.1 · Status: Draft · 2026-09-27

A security kernel is itself a high-value target. This document treats the kernel as the attacker's prize and specifies its defense accordingly.

## 1. The sandbox namespace (the kernel's entire reach)

| Resource | Identifier | Purpose |
|----------|------------|---------|
| DynamoDB | `antares-demo-ledger` | demo mutation target (synthetic entitlement records) |
| S3 | `antares-demo-vault-846719` | versioned demo objects, evidence archive |
| SSM | `/antares/demo/*` | demo parameters (including the honeypot endpoint value) |

The kernel's IAM roles carry `Resource` scoping to exactly these ARNs plus its own table, bucket and log groups. There is no role, policy variable, or code path that widens this scope. The claim is testable: the launch checklist (section 6) includes an attempted out-of-scope mutation that must fail with `AccessDenied`, and that test runs in CI against a cloned role.

## 2. Threat model (STRIDE, applied to the kernel)

| Threat | Vector | Control |
|--------|--------|---------|
| Spoofing | Fake agent identity submitting calls | API keys + usage plans; agent identity recorded per call; key rotation documented |
| Tampering | Altered verdicts or receipts | Merkle chain over canonical records; daily S3 anchors; client-side verification |
| Repudiation | "The kernel did it, not us" | Every call, approval and bypass is ledgered with principal and ts; CloudTrail covers every AWS call |
| Information disclosure | Verdicts leaking account internals | RFC 7807 errors with registered codes; no stack traces, no account ids in public surfaces |
| Denial of service | Kernel hammered to force fail-open chaos | Fail behavior is policy (reads allow-with-flag, mutations halt); throttling at the edge; load test in doc 14 |
| Elevation of privilege | Bypass token theft; kernel prompt injection | Tokens: KMS-signed, single-use, 60 s, bound to verdict and call ids. Prompts: the closed-inputs rule (doc 05 section 6); kernel prompts carry hashes and findings, never raw untrusted payloads |

## 3. The kernel's own inputs

S0 screens content headed anywhere in the pipeline, including the quorum prompts. Prompts are assembled from fixed templates plus hash references; an attacker who controls document content controls, at most, a hash string arriving at a model. Prompt-injection against the quorum is itself an evaluated attack class in doc 07.

## 4. The honeypot secret

A synthetic secret in Secrets Manager, named to attract (the demo's `get_secret` target). It is fake, labeled fake in the receipt, and its "leak" lands in our own trap Lambda, not any external endpoint. Purpose: the visible, memorable proof that perimeter plus tripwire catch a compromised agent mid-exfiltration.

## 5. Data classification and privacy

All data in the namespace is synthetic and classified PUBLIC-DEMO. No personal data, no customer data, no real credentials anywhere in the system. Decision retention 90 days, vault 1 hour, metrics 180 days (doc 06). The privacy story is short because the design refuses to collect the data in the first place.

## 6. Launch checklist (gates, all must pass)

1. Out-of-scope mutation test fails with `AccessDenied` (CI-verified against cloned role).
2. Kill switch (`ANTARES_HALT`) halts all classes within one in-flight call; drill recorded.
3. Budget alarm fires at the configured threshold; drill recorded.
4. Vault-absence test: mutating call without pre-captured state is refused.
5. Bypass token: reuse rejected, expiry rejected, wrong-verdict rejected.
6. Merkle verification: console and SDK verify the same receipt, hashes match.
7. Public surfaces expose no account identifiers beyond the sandbox ARN names.
8. CloudTrail proof pack assembled (also feeds the hackathon agent-connection evidence).

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

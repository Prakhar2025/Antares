# Doc 16: Glossary

Version 0.1 · Status: Draft · 2026-09-27

Normative definitions. Where code and glossary disagree, one of them is a defect (doc 05 rule).

| Term | Definition |
|------|------------|
| Kernel | The Antares runtime: the only path by which a gated tool call reaches AWS |
| Gate (S2) | The deterministic code check with veto power: schema, shell tokenizer, ARN allowlist, class weights. No model involved |
| Quorum (S3) | The two-model judgment on escalated calls: blast-radius reasoner plus adversarial red-teamer, fused deterministically |
| Adversary | The red-team model in the quorum; cross-vendor by design; default set by the doc 07 A/B winner |
| Disagreement score | Normalized variance across the quorum's risk scalars; above threshold it forces ABSTAIN, never an average |
| Blast radius | resource count x severity weight x (1 - reversibility); inputs measured from live read-only probes, never estimated by a model |
| Probe (S4) | A read-only Describe/List call that extracts radius inputs from actual AWS state |
| Saga (S5) | The compensating-transaction pattern: pre-capture to vault, commit, reverse and verify on demand |
| Vault | The TTL-bounded store of pre-captured prior state; no vault entry, no commit |
| Perimeter (S0) | Input screening: normalization, signatures, classification, tripwires; screens content before any consumer trusts it |
| Tripwire | A canary planted in tool output or documents; any agent echo fires an incident |
| Canary | A generated token no legitimate agent should ever repeat |
| Verdict | The kernel's decision: ALLOW, HARD_BLOCK, or ABSTAIN, always with evidence and a named fusion rule |
| ABSTAIN | Suspended judgment with a signed, single-use, 60-second bypass token; never an average of votes |
| Bypass token | KMS-signed, single-use, expiry-bound approval artifact; its use is itself a ledger event |
| Merkle receipt | Hash-chain record of a decision or action, verifiable client-side; anchored daily to S3 |
| Fast path | Gate-only evaluation; clean read-class calls skip models entirely |
| Escalated path | Quorum plus probes plus vault; the deep path for anything mutating or suspicious |
| Sandbox namespace | The exact resource set the kernel's IAM can touch (doc 08); the kernel's entire reach |
| Fail loud | The documented non-default failure behavior: mutations halt when unjudgeable; reads allow-with-flag |
| Adversarial-benign | Content that looks attack-shaped and is not; the false-positive slice of the corpus |

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

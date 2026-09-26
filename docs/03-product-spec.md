# Doc 03: Product Spec

Version 0.1 · Status: Draft · 2026-09-27

## Personas

**P1, the agent developer.** Ships an agent that touches AWS. Wants one SDK call and honest latency. Success: integrated in under five minutes, never surprised by a verdict, every block comes with a reason they can act on.

**P2, the platform or security owner.** Owns the account the agents run in. Wants policy they can read, receipts they can audit, and proof the kernel cannot widen its own permissions. Success: can state exactly what the kernel may touch, and show a hash chain for any incident.

**P3, the evaluator or visitor.** No credentials, no patience, evaluating dozens of projects. Success: understands the entire system from one ten-second interaction on a public URL, with zero login.

## Journeys

**J1, integrate (P1):** install SDK, wrap the tool dispatcher with `kernel.gate(call)`, get verdicts with evidence. Blocked actions return a machine-readable diagnosis the agent can self-correct from.

**J2, evaluate (P3):** open the public console, click one of three preset scenarios (benign, injected, destructive), watch the gate, the quorum votes, the blast-radius math, and either the block or the live rollback, then verify the Merkle receipt client-side.

**J3, respond (P2):** an incident lands (tripwire fire or hard block on an escalated action), the owner sees the evidence bundle, either approves a single-use bypass or lets the saga reversal stand.

## Features and acceptance criteria

| ID | Feature | Acceptance criterion |
|----|---------|---------------------|
| F1 | Perimeter screening (S0) | Untrusted content passed to `screen()` returns a verdict with per-layer findings; obfuscated payloads (homoglyph, zero-width, base64) are normalized before matching; benign scary content (security prose discussing attacks) is not blocked at the perimeter. |
| F2 | Deterministic action gate (S2) | Every mutating call is checked against tool schema, shell tokenizer, ARN allowlist and severity weights in pure code; a code BLOCK short-circuits all model calls; measured gate latency under budget (doc 17). |
| F3 | Cross-vendor consensus quorum (S3) | Escalated calls produce two independent model votes (blast-radius reasoner, adversarial red-teamer) with a computed disagreement score; the fusion rule is deterministic and published; the adversary is configurable and the shipped default is the doc-07 benchmark winner. |
| F4 | Live blast-radius probes (S4) | Radius inputs come from read-only Describe/List calls against live state (item counts, versioning status, PITR status); the radius formula is deterministic and shown in the verdict. |
| F5 | Saga rollback (S5) | Every mutation pre-captures state to a TTL vault before commit; rollback restores the prior state and verifies it; the demo shows a real mutation reversed live with byte-identity asserted. |
| F6 | Tripwire canaries (S0) | Canary sets can be generated and planted in tool outputs and documents; any agent echo of a canary raises an incident event; the public console shows the incident feed. |
| F7 | Three-state verdicts with bypass (S3) | ALLOW, HARD_BLOCK, and ABSTAIN (suspended with a signed, single-use, 60-second bypass token); bypass usage is itself ledgered. |
| F8 | Merkle receipts (S6) | Every decision and action produces a receipt verifiable client-side from the console; the chain root is anchored daily. |

## Explicit scope cuts for the build window

- Multi-account and cross-organization role assumption: enterprise tier, not built.
- Compute-class mutations (EC2 lifecycle, EKS): the probe library covers DynamoDB, S3, SSM and Lambda configuration classes only.
- Real customer data: none, ever. Demo resources carry synthetic data only.
- Kubernetes and non-AWS clouds: not built.

Each cut maps to a roadmap era (doc 11) and is stated on the record, not hidden.

## Non-goals

Antares does not read agent reasoning, does not conversationally coach agents, and does not move money or send messages of any kind. It gates, measures, reverses, and attests. Nothing else.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

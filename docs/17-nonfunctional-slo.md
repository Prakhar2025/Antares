# Doc 17: Non-Functional Requirements and SLOs

Version 0.1 · Status: Draft, all values are design budgets until doc 07 back-fills measured tables · 2026-09-27

## Latency budgets

| Path | p50 | p95 | Composition |
|------|-----|-----|-------------|
| Fast path (gate only, read class) | 120 ms | 900 ms | API GW + Lambda cold/warm + in-process gate |
| Screen (S0, sync) | 250 ms | 1.2 s | signatures always, classifier on flag |
| Escalated path (quorum + probes) | 1.5 s | 3.5 s | parallel votes and probes; presented async in the console |
| Rollback (trigger to verified restoration) | under 60 s end to end | n/a | saga proof, byte-identity asserted |

Budgets are contracts with the product shape: if the fast path cannot hold, inline adoption dies; if escalation cannot hold, it becomes async-only. Misses are handled by formal revision in this doc, never by silent threshold drift.

## Availability and the error budget

| SLO | Target | Window |
|-----|--------|--------|
| Console and public API availability | 99.5 percent | launch window |
| Mutation-gating availability | 100 percent reachable (halt is a valid, loud answer) | always |

Error budget policy: a failed SLO freezes feature phases until the cause is ledgered and fixed. Fail-loud states (halt) count as available because they are the documented safe behavior, not outages.

## Capacity math (design estimate, launch-window scale)

Expected public traffic: three presets, visitor bursts, eval batches of 300 calls. Per-escalated-call Bedrock cost and the blended cost per gated action are measured in P5 (doc 07). Provisioned nothing: on-demand DynamoDB, ARM Lambda, no containers. Concurrency headroom: Lambda default account concurrency is the limiter; reserved concurrency is not needed at this scale and adds a failure mode.

## Data classification

| Class | Where | Handling |
|-------|-------|----------|
| PUBLIC-DEMO | everything in the sandbox namespace and console | synthetic only, safe to show |
| OPERATIONAL | decisions, receipts, metrics | 90 to 180 day retention (doc 06), KMS-encrypted |
| SECRET-class | the demo honeypot value | fake, labeled fake, trap Lambda destination; Secrets Manager storage for ceremony |

No personal data, no customer data, no real credentials: the classification table is short because the design refuses the data (doc 08 section 5).

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

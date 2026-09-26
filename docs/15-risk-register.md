# Doc 15: Risk Register

Version 0.1 · Status: Draft · 2026-09-27

Scored L x I on 1 to 5 (likelihood, impact). Review cadence: at every phase exit. Early warning = the observable that says the risk is materializing.

| ID | Risk | L | I | Score | Mitigation | Early warning |
|----|------|---|---|-------|------------|---------------|
| R1 | Visitor misses the depth: sophisticated kernel, ten-second attention | 4 | 5 | 20 | the ten-second demo path is a product requirement (doc 10); video leads with the kill and the reversal, not architecture | any person who needs more than one minute to get it |
| R2 | Latency budgets blow: escalated path too slow for inline use | 3 | 4 | 12 | fast path carries the majority by design; escalation presented async (doc 10); budgets measured in P1, revised formally if missed | P1 gate latency above budget |
| R3 | Demo mutation escapes the sandbox namespace | 1 | 5 | 5 | IAM Resource scoping, out-of-scope CI test (doc 08 checklist 1), kill switch, rehearsal drills | any AccessDenied anomaly or unscoped ARN in CloudTrail |
| R4 | Benchmark overfit or corpus leakage inflates results | 2 | 5 | 10 | held-out discipline (doc 07 section 5), corpus checksummed in CI, thresholds tuned on dev split only | suspiciously perfect metrics; dev/test split audit |
| R5 | Cost overrun on Bedrock during eval or visitor traffic | 3 | 2 | 6 | budget alarm at start (doc 08), batched eval, fast path model-light | alarm fire; daily cost check |
| R6 | Last-day competitor surge with a comparable kernel | 3 | 4 | 12 | launch URL live day 3; moats are depth, live rollback, published benchmark, meta-position (the competitor's agent needs a kernel) | comparable public project appearing on the projects feed |
| R7 | Model access changes mid-window (quota, region, agreement) | 2 | 4 | 8 | all model ids config-driven (doc 04); adversary A/B covers four families; degraded modes tested in chaos drills | any invoke AccessDenied in CI |
| R8 | The kernel becomes the attack surface (bypass theft, prompt injection into quorum) | 2 | 5 | 10 | single-use 60 s signed tokens; closed-inputs rule; injection classes in the corpus; doc 08 threat model reviewed at P2 exit | red-team drill findings at P2 |
| R9 | Deadline compression: phases slip into the buffer | 3 | 3 | 9 | launch gate live at P3 regardless of P4 polish; buffer days reserved; scope cuts pre-agreed (doc 03) | phase exit dates slipping past day boundaries |
| R10 | Account-level blocker (billing instrument, service quota) breaks deploy | 2 | 4 | 8 | Amazon-native only, no marketplace dependencies; direct-id versus regional-profile model handling documented (doc 09 runbook) | any new AccessDenied class in deploys |

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

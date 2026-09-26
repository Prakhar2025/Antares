# Doc 11: Roadmap

Version 0.1 · Status: Draft · 2026-09-27

## Build phases (hackathon window, owner reviews each gate)

| Phase | Content | Exit gate |
|-------|---------|-----------|
| P0 | This documentation suite reviewed and Locked | owner review; only Locked docs gate code |
| P1 | Kernel gateway (S1) + deterministic gate (S2) + tool registry + policy config; unit-tested; dev namespace deploy | gate latency measured under budget; veto test green |
| P2 | Quorum (S3) + disagreement metric + three-state verdicts + bypass tokens | escalated path live end to end on dev |
| P3 | State probes (S4) + radius math + saga engine (S5) + vault; **public ship-gate URL live** | real mutation executed and rolled back live; receipts written |
| P4 | Console (S7) on CloudFront: dispatcher, telemetry, incidents, receipts | zero-login judge path green on prod namespace |
| P5 | Evaluation: corpus finalized, baselines + adversary A/B + McNemar; BENCHMARK.md published with measured tables | doc 07 bars met or missed in public; doc 07 back-filled |
| P6 | Proof pack (CloudTrail agent evidence), pitch video per doc 12, submission text with tags, hardening drills from doc 08 checklist | submission ready before deadline day; two buffer days held |

Phase loop inside every phase (doc 14): code, test, review, what-broke entry for every failure, fix, status update, conventional commit, push. No phase starts on a red previous phase.

## Eras beyond the window

| Era | Content | Why it follows |
|-----|---------|----------------|
| E1, open launch | Apache 2.0 core, Python + TypeScript SDKs, benchmark corpus published, engineering writeup | adoption and scrutiny; the core is already designed to be inspected |
| E2, enterprise | multi-account Control Tower governance, org policy packs, RBAC/IdP integration, compliance audit exports, S3 Object Lock anchoring | the paid tier from doc 01, built on the same contracts |
| E3, ecosystem | policy-as-code packs for agent governance, marketplace of tool registries, partner integrations on EventBridge | the kernel becomes the place where agent policy lives |

## Deliberately out of scope (standing)

Compute-class mutations (EC2/EKS), non-AWS clouds, real customer data, agentic money movement of any kind. The kernel gates, measures, reverses and attests; the roadmap never widens that charter.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

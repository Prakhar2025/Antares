# Phase Log

> One row per phase (doc 11). Evidence links point at commits, live endpoints
> and measured numbers. A phase is Done only when its exit gate is met and
> the evidence is recorded here.

| Phase | Scope | Status | Exit evidence |
|-------|-------|--------|---------------|
| P0 | Documentation suite reviewed and locked | In review | suite v1.0 on GitHub, owner feedback applied (commits 1f2dbea, 3fbf900) |
| P1 | Kernel gateway S1, deterministic gate S2, tool registry, policy, dev deploy | **Done, awaiting owner sign-off** | see below |

## P1 evidence (2026-09-27)

- Live dev endpoint: https://gmbvgf4mwj.execute-api.us-east-1.amazonaws.com/dev (API-key gated, usage plan 20 rps / 5000 per day)
- Stack `antares-dev`: ARM64 python 3.12 Lambda, DynamoDB single table with SSE and 90 day TTL, 7 day log retention, least-privilege IAM scoped to one table
- Verdicts demonstrated live: ALLOW (clean read), HARD_BLOCK (shell metacharacter, rule GATE-SHL-001), ABSTAIN (destructive class, rule GATE-ESC-001)
- Decision persistence: dual-write single table, verdict fetch roundtrip verified live
- Measured gate latency (in-Lambda, 6 calls): 22 to 34 ms, p50 about 23 ms, against the doc 17 fast-path budget of 120 ms p50: **met**
- Wall-clock from Nagpur to us-east-1: 0.8 to 1.7 s (round-trip geography, not kernel time; edge measurement arrives with the console in P4)
- Test suite: 39 tests, 97.4 percent coverage, ruff and mypy strict green, CI workflow active on GitHub
- Kill switch present: ANTARES_HALT returns 503 kernel-halted (unit-tested)

## Quorum milestone evidence (2026-09-27)

- Live destructive call judged by the real cross-vendor quorum: Llama 3.3 70B risk 0.2 ("suspicious key pattern") versus Nova Pro risk 0.1 ("routine read on a development table"), divergence 0.1, fused ALLOW in 940 ms, 479 input plus 68 output tokens
- Live attack call (instruction override hidden in a delete key): HARD_BLOCK via QUORUM-BLK-001; adversary risk 0.99 "instruction override detected", reasoner risk 0.95 "high risk of data loss and security breach", divergence 0.04, 596 ms; perimeter had already flagged OVR-001 on the parameters
- Screen endpoint live: hostile text returns HOSTILE with OVR-001 plus EXT-001 and semantic risk 0.95 (Nova Lite)
- Canary tripwire live: canary created, echoed output fired TRIPWIRE_FIRE, incident visible in the feed
- Bypass flow: ABSTAIN verdicts issue a KMS-signed single-use 60-second token in the x-antares-bypass-token response header; redemption, replay rejection and incident recording are covered by unit tests (live ABSTAIN is model-dependent)
- Escalated-call latency measured 596 to 940 ms against the doc 17 escalated budget of 3.5 s p95: **met**

## Reversal milestone evidence (2026-09-27)

- Blast-radius probes live: mutating calls measure live state before executing (item existence, table counts, PITR status, S3 versioning, SSM existence); unknown radius escalates to max severity
- Full saga cycle demonstrated live on the real stack: gated DELETE of customer#4829 (quorum votes 0.0 adversary / 0.3 reasoner, radius 0.5) executed, item removed from the live table, then ROLLBACK restored it with byte-identity verified and tier ENTERPRISE confirmed by a direct AWS read
- Merkle receipts live: action and rollback records chained (leaf 84d069bc chained to prev 382da0b3); client-side verification rule published
- Metrics endpoint live: per-day counters (12 verdicts on day one)
- Attack library endpoint live: 16 named signature classes
- Deployment pipeline hardened: bundle verification assert, automatic API restage on every deploy, pip index pinned away from the machine's broken mirror, quoted interpreter paths
- What-broke ledger grew by five entries; every one carries a prevention rule

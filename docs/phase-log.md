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

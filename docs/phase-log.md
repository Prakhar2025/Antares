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

## Console milestone evidence (2026-09-27)

- Ship-gate public URL live: https://d3jhd66xz9xj9.cloudfront.net (verify the exact id against the stack output; console at /console)
- Zero-login judge path proven: landing 200, console 200, CORS preflight 200, gate POST 200 from the site origin
- The console dispatcher runs four preset scenarios against the real stack: benign ops (ALLOW, gate 0-1 ms), clean write (ALLOW with live quorum votes), poisoned write (HARD_BLOCK, perimeter OVR-001 plus quorum conviction), destructive delete (ABSTAIN or ALLOW by quorum judgment)
- Deployment pipeline: static export built with the API URL baked in, synced to the site bucket, CloudFront with index-resolution function, automatic restage on deploy
- What-broke ledger: OAC resource rejected by the account early-validation hook (bisected via probe stacks; classic public-read bucket policy adopted), mock integrations need request templates (mock 500 lesson), S3 sync backslash keys verified clean

## Benchmark milestone evidence (2026-09-27)

- 300-case corpus generated and committed (evals/corpus.jsonl via evals/corpus.py, seed-stable): 150 benign (including 44 adversarial-benign) and 150 adversarial across six named classes
- Fused pipeline (default adversary Llama 3.3 70B): not-allowed recall 1.0, hard-block recall 0.7, benign FPR 0.193 (target 0.035: missed and published with the named regression), 133 s wall
- Adversary A/B complete: Llama 3.3 (1.0/0.193/133 s) shipped over Maverick (0.98/0.313), GPT-OSS (0.973/0.16), DeepSeek R1 (0.967/670 s)
- McNemar fused versus code-only: b=6, c=15, p=0.078, with the mechanism analysis published
- BENCHMARK.md published; doc 07 back-filled to version 0.2; one public URL serves the console and the metrics
- Live direct DynamoDB put verified the ledger head conditional-put lesson (untyped ts caught by ParamValidationError, fixed and ledgered)

## Launch milestone evidence (2026-09-27)

- CloudTrail proof pack assembled (docs/submission/proof-pack.json, generated by the committed scripts/assemble_proof.py): the agent's own Bedrock Converse calls, Lambda deployments, API Gateway and DynamoDB operations recorded by AWS across the build window
- Kill switch drill PASSED live: ANTARES_HALT=true produced 503 kernel-halted through the public URL, revert restored the 200 gate
- Out-of-scope drill PASSED: a foreign-table delete rejected at the gate by GATE-ARN-001 with the class finding attached
- Budget alarm live: antares-dev-cost-cap, USD 10 per month
- Submission text finalized (docs/submission/project-page.md) with tags, the honest benchmark numbers and the proof-pack links
- README updated with the live URLs and the benchmark link

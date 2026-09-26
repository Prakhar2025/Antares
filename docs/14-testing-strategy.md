# Doc 14: Testing Strategy

Version 0.1 · Status: Draft · 2026-09-27

## Test pyramid

| Layer | What | Notes |
|-------|------|-------|
| Unit (majority) | gate rules, shell tokenizer, radius math, fusion rules, Merkle canonicalization, canary matching | fusion rules and radius math are property-tested; a rule that fires must be named (doc 05 section 4) |
| Contract | boto3 fakes mirror real return shapes exactly | the ledger lesson: `bool(resp.get("Attributes"))` class bugs die here; every fake method asserts its shape against the real client in CI |
| Integration | full pipeline against the dev sandbox namespace: real probes, real vault, real rollback | runs on every merge; prod namespace only for release drills |
| Chaos drills | Bedrock perms revoked mid-call; DynamoDB throttle; adversary timeout; vault write failure | asserts the failure matrix of doc 04, not hopes about it |
| Evaluation | doc 07 corpus as a test suite | results are artifacts with dates, never conversation |

## CI gates (merge blockers)

ruff (strict), mypy (strict), pytest with coverage gate at 90 percent, gitleaks with full checkout depth, schema-drift check on doc 05 schemas versus code, corpus checksum verification (doc 07 honesty rule).

## The phase loop (how every phase of doc 11 runs)

1. Code the phase slice against the Locked docs only.
2. Test to the gates above; green locally.
3. Review the diff (self-review pass, then owner pass at phase exit).
4. Any failure, any layer: what-broke.md entry the same day (symptom, root cause, fix, prevention, phase).
5. Fix, re-run, status update in the phase log, conventional commit, push.
6. Phase exit: owner reviews the exit gate evidence; only then does the next phase start.

No phase starts on a red previous phase. No failure bypasses the ledger. A failure without a prevention rule is an unfixed failure.

## Definition of done (any feature)

Docs satisfied, tests green in CI, latency within doc 17 budgets or the budget formally revised, what-broke clean for the slice, docs updated with any behavioral delta, conventional commit history that reads as the story of the change.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

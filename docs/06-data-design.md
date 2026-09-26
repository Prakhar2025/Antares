# Doc 06: Data Design

Version 0.1 · Status: Draft · 2026-09-27

## Single-table layout (DynamoDB `antares-main`)

| Entity | PK | SK | Body (abridged) | TTL |
|--------|----|----|------------------|-----|
| Config | `TENANT#default` | `CONFIG#policy` | thresholds, adversary model id, class weights, fail policy | no |
| Decision | `TENANT#default` | `DECISION#{iso_ts}#{verdict_id}` | full Verdict (doc 05 schema 3) | 90 days |
| Action | `TENANT#default` | `ACTION#{action_id}` | executed call record, probe snapshot refs, receipt root | 90 days |
| Vault | `TENANT#default` | `VAULT#{action_id}` | pre-captured prior state: exact item image, parameter version, S3 version ids | 1 hour |
| Canary | `TENANT#default` | `CANARY#{canary_id}` | token, planted ref, created_by, status | no |
| Incident | `TENANT#default` | `INCIDENT#{iso_ts}#{incident_id}` | kind, refs, evidence bundle pointer | 90 days |
| Metrics | `TENANT#default` | `METRICS#{yyyy-mm-dd}` | counters: calls, verdicts by state, class, latency percentiles, cost estimate | 180 days |

Access patterns are served by the dual-write layout (no GSIs: the
account-level early-validation hook rejects GSI creation, recorded in
what-broke). Every decision writes two items: the lookup item
(`pk = VERDICT#{id}`) and the state feed item (`pk = STATE#{state}`).
Incidents (P2) write `pk = INCIDENT#{kind}`; daily metrics (P3) write
`pk = METRICS#{date}`.

Access patterns to prove in tests: verdict by id (GetItem on the lookup item); recent verdicts by state (Query on the feed item); incidents by kind (Query); vault fetch by action id (single-digit ms, saga-critical); daily metrics rollup; canary status flip.

## The state vault (saga-critical)

Before any mutating call commits, S5 writes the exact prior state: full DynamoDB item image (with consistent read), SSM parameter version, or S3 version listing. Vault entries carry 1-hour TTL: long enough for any rollback in the window, short enough that the vault never becomes a shadow copy of the namespace. Rollback consumes the vault entry atomically (conditional delete) so a reversal cannot double-fire.

## Merkle chain (tamper-evident provenance)

Leaf: `sha256(canonical_json(decision_or_action_record))` with a fixed field order (canonicalization spec in the SDK). Each leaf stores `{leaf_hash, prev_leaf_hash, ts}`; the running root is re-computed on write and anchored to S3 daily under `anchors/yyyy-mm-dd.json` (KMS-encrypted). Client-side receipt verification recomputes hashes from the canonical record only; the console ships the verifier, and the SDK ships the same code. Roadmap era 2 replaces daily anchoring with S3 Object Lock compliance mode.

## Evidence storage (S3)

`evidence/{verdict_id}/bundle.json`: probe outputs, vote payloads, gate findings, prompt-response hashes (content itself is not persisted beyond what the corpus requires; doc 08 covers retention). Bucket: versioning on, KMS CMK, no public access, lifecycle to cold storage at 90 days.

## What is deliberately not stored

No agent conversation transcripts, no user identifiers, no real customer data. The demo secret is a synthetic value generated for the sandbox. Retention is 90 days for decisions and incidents, then expiration by TTL, because a security product that hoards data is its own liability.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.2 | 2026-09-27 | P1 build: GSIs replaced by the dual-write lookup and feed pattern after the account early-validation hook rejected GSI creation (what-broke). |
| 0.1 | 2026-09-27 | Initial draft for owner review. |

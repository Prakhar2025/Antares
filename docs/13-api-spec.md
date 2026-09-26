# Doc 13: API Spec

Version 0.1 · Status: Draft · 2026-09-27

Base: `https://{api-id}.execute-api.us-east-1.amazonaws.com/v1` · Auth: API key (usage plans) for integrators; the console's own paths are server-side and keyless. All bodies JSON; all errors RFC 7807 problem+json with a registered code.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/screen` | S0 perimeter screening of untrusted content; fast path, sync |
| POST | `/gate` | Submit a ToolCall (doc 05 schema 2); returns Verdict; sync on fast path, async with decision id on escalation |
| GET | `/decisions/{verdict_id}` | Full Verdict with evidence bundle pointer |
| POST | `/decisions/{verdict_id}/bypass` | Redeem a signed bypass token for an ABSTAIN verdict; single-use, 60 s |
| GET | `/actions/{action_id}/receipt` | Merkle receipt + canonical record for client-side verification |
| POST | `/canaries` | Generate a canary set for a tool output or document |
| POST | `/tripwire/check` | Check agent output for canary echoes; returns incident if fired |
| GET | `/metrics` | Live counters and measured latency percentiles |
| GET | `/attacks` | The machine-readable attack library behind the console dispatcher |

## Error registry (RFC 7807)

| Code | Title | HTTP | Meaning |
|------|-------|------|---------|
| `schema-rejected` | ToolCall failed schema validation | 422 | fix the call; no models were run |
| `code-veto` | Deterministic gate blocked the call | 403 | findings list names every rule |
| `unknown-tool` | Tool not registered | 404 | register the tool first |
| `verdict-not-found` | Unknown decision id | 404 | ids are single-use scoped |
| `bypass-invalid` | Token expired, reused, or wrong verdict | 403 | request a new suspension |
| `kernel-halted` | Kill switch engaged | 503 | fail-loud state, doc 08 |
| `rate-limited` | Usage plan throttle | 429 | back off; plan limits documented |
| `internal` | Unexpected kernel error | 500 | no stack traces, no account identifiers |

## Event schemas (EventBridge bus `antares-bus`)

```
antares.decision v1 {verdict_id, state, action_class, radius_score, latency_ms, merkle_root, ts}
antares.incident  v1 {incident_id, kind, refs[], ts}
```

Consumers own their retry policy; the kernel guarantees at-least-once delivery and idempotent consumers are the integration requirement (documented in the SDK).

## Versioning

Path-versioned (`/v1`). Additive changes only within v1; breaking changes open v2 and v1 ships for its documented lifetime. The Verdict and ToolCall schemas carry explicit `schema_version` fields (doc 05).

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

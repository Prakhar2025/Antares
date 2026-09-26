# What Broke: The Failure Ledger

> Append-only. One entry per real failure, the day it happens. Never edited retroactively, never deleted. This file is the honest cost of the build and the first thing read before trusting any benchmark number in doc 07.

Version 0.1 · Status: Active · 2026-09-27

## Entry format

```
## [YYYY-MM-DD] <short title>
Symptom: what was observed, with the exact error or wrong output.
Root cause: the actual cause, not the surface.
Fix: what changed, with file or resource names.
Prevention: the rule, test or gate that stops recurrence.
Phase: which build phase (P0 to P6, doc 11).
```

## Entries

(none yet, the build has not started, docs are in review)

# Doc 12: Pitch and Launch Plan

Version 0.1 · Status: Draft · 2026-09-27

## Video script skeleton (target 2:30 to 3:00, demo-first)

| Beat | Time | Shot | Content |
|------|------|------|---------|
| Cold open | 0:00 to 0:15 | screen: console dispatcher | "An agent is about to delete production state. Watch." Click the injected scenario. |
| The kill | 0:15 to 0:45 | split: telemetry stream | Code gate findings, two model votes streaming, disagreement score, HARD_BLOCK, tripwire fires |
| The reversal | 0:45 to 1:15 | screen: destructive scenario | Real mutation commits, post-flight detection, saga rollback, byte-identity assertion shown |
| The receipt | 1:15 to 1:35 | screen: receipts page | Client-side Merkle verification, hashes recomputing in the browser |
| The numbers | 1:35 to 2:00 | screen: benchmarks page | Measured tables with dates: recall, FPR, latency, cost, adversary A/B winner, McNemar result |
| The architecture | 2:00 to 2:25 | diagram overlay | One diagram, seven subsystems, the AWS service map, "models propose, code decides" |
| Close | 2:25 to 2:45 | talking head or text card | Author, arc (TruthLayer, Gatehouse, Antares), live URL on screen |

Recording quality: script read aloud before recording (doc 20-style discipline from the author's prior suite), no dead air, every cut under 4 seconds, captions burned in.

## Launch checklist

- Category tag `#workplace-efficiency`, lane tag `#startups`, set on the public project page before the announcement.
- Live public URL: on the project page and in the first line of the description.
- Documented proof of the coding-agent connection: CloudTrail evidence pack (the agent's own API calls building the stack), devlog, what-broke.md linked as the honest build ledger.
- Development process section: phases P0 to P6 with dates, the adversary A/B story, and the two-agent architecture review (the decision record from docs 18).
- Originality statement: no prior publication; portfolio lineage (TruthLayer, Gatehouse, Sentinel) disclosed as context, not reused code.
- All claims on the page traceable to docs 07 and 17; no unmeasured number appears anywhere.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

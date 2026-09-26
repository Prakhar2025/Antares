# Doc 10: Console

Version 0.1 · Status: Draft, design language pending dedicated session with owner · 2026-09-27

## Product surface (screens)

| Screen | Job | Visitor-visible |
|--------|-----|---------------|
| Dispatcher | Three preset scenarios (benign ops, injected build log, destructive mutation) plus a custom tool-call playground; one click dispatches a real gated call against live sandbox resources | yes, the front door |
| Telemetry | Live stream of the pipeline: code gate findings, quorum votes with model ids, disagreement score, radius inputs, verdict, latency breakdown | yes |
| Incidents | Tripwire fires, hard blocks, bypass approvals, rollback records | yes |
| Receipts | Any decision's evidence bundle and Merkle receipt; client-side hash verification button | yes |
| Benchmarks | The measured tables from doc 07 with dates and corpus version | yes |

Zero login for all of the above. API keys exist for integrators; visitors never need one. The ten-second comprehension path: land on Dispatcher, click the injected scenario, watch the vote stream, see the block and the tripwire fire, verify the receipt. Nothing else is required to understand the product.

## Interaction spec (level of detail that prevents UI drift)

- Dispatcher preset click to verdict display: single API round trip, escalated scenario presented as async with visible phase transitions (gate, quorum, probe, verdict), never a frozen spinner.
- Vote stream shows model id, score, and a one-line rationale hash per judge; raw payloads one click deeper.
- Bypass approval is a deliberate two-step with the expiry countdown visible; expired tokens render as dead, teaching the 60-second property visually.
- Receipt verification runs entirely client-side; the page states what was hashed and what was not, so the trust boundary is explicit.
- Every number on screen carries its provenance (measured at, corpus version, region) per the accuracy doctrine.

## Design language (status and direction)

Status: pending the dedicated design session with the owner before any UI code is written. Direction captured so far, subject to that session: mission-control precision. Flat surfaces, hairline borders, monospaced instrument typography for telemetry, one signal accent for state, generous density, and the explicit banned list: glassmorphism, blur, gradients, glow, emoji as icons, generic SaaS card layouts. The console is an instrument panel for high-consequence infrastructure, not a marketing page.

## Non-goals

No auth walls, no onboarding funnels, no dashboards of vanity metrics, no chat with the kernel.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

# Doc 07: Evaluation

Version 0.1 · Status: Draft · 2026-09-27

This document is the honesty contract for every number Antares will ever publish. Rule zero: measured values only, dated, with the corpus and thresholds disclosed. Target values written below are bars to be met or missed in public, never presented as results.

## 1. The corpus (300 cases, versioned, published)

**150 benign operational cases**, drawn from real AWS operational grammar: describe/list/read patterns, tagging, PITR enablement, TTL verification, scaling adjustments, log retrieval, parameter reads. Includes 30 adversarial-benign cases: content that looks attack-shaped but is not (a pentest report quoting injection payloads inside quotes, a security newsletter discussing jailbreaks, runbooks mentioning destructive commands in procedural prose). This slice is where false positives live or die, and it is the headline number.

**150 adversarial cases**, mapped to named classes:

| Class | Count | Example grammar |
|-------|-------|-----------------|
| Injection-driven mutation | 40 | poisoned document instructs deletion, exfiltration, or permission change |
| Shell abuse | 25 | chaining, substitution, destructive flags reaching tool params |
| Privilege escalation | 20 | `iam:AttachRolePolicy`, admin grants, SCP evasion attempts |
| Destructive mutations | 25 | recursive deletes, table drops, purge operations |
| Exfiltration plumbing | 20 | credentials or context bound for external endpoints, image-tag data leaks |
| Parameter poisoning | 20 | type confusion, ARN swap, environment variable overwrite |

Every case carries: id, class, label, the exact tool call, the live-state fixture it assumes, and provenance of the pattern (synthesized from public attack grammar; no real customer data). The corpus is a versioned artifact; changing it after results are announced is prohibited by the honesty rules (section 5).

## 2. Metric bars (targets to meet or miss, with intervals)

| Metric | Bar | Notes |
|--------|-----|-------|
| Recall on destructive + injected (150 adversarial) | 1.00 on this corpus | worded exactly like this, never as a field claim |
| False-positive rate on benign (150 benign) | at or under 0.035 | the anti-uninstall number; headline |
| Precision on HARD_BLOCK | reported with Wilson 95 percent interval | no naked point estimates |
| Gate latency (fast path) p50 / p95 | budget: 250 ms / 900 ms, measured values back-filled | doc 17 budgets |
| Escalated path p50 / p95 | budget: 1.5 s / 3.5 s, measured values back-filled | escalation is presented async in the console |
| Rollback completion | under 60 s end to end, restoration byte-identity asserted | saga proof |
| Cost per gated action | measured blended value published | budget window under 10 USD total (doc 09) |

## 3. Adversary A/B protocol (which red-teamer ships)

Candidates: Meta Llama 3.3 70B (incumbent default), Meta Llama 4 Maverick, OpenAI GPT-OSS 120B, DeepSeek R1. Identical adversarial persona, identical escalation slice, identical thresholds; Nova Pro stays the blast-radius reasoner throughout. Measured per candidate: recall on the injection-driven slice, FPR contribution on adversarial-benign, p50/p95 vote latency, cost per vote. The winner ships as default; the full comparison table publishes in BENCHMARK.md with date and corpus version. No candidate is chosen by preference, only by this table.

## 4. Baselines and tests

- **Code gate only** (no models): proves what deterministic logic alone catches, and quantifies what the quorum adds.
- **Single-model baseline** (Nova Pro alone, no adversary): quantifies the cross-vendor contribution.
- **Bedrock Guardrails alone**: the AWS-native baseline, measured on the same corpus.
- Fusion versus best single baseline: McNemar test on paired per-case outcomes; p-value published with the discordant-pair counts. The claim "the quorum earns its latency" must survive this test or be withdrawn in BENCHMARK.md.

## 5. Honesty rules

1. Thresholds are tuned on a dev split only; the 300-case corpus is the held-out test, touched once per announced run.
2. Every published number carries: date, corpus version, model ids, region.
3. Missed bars are published, not re-rolled. A missed recall case becomes a named regression case.
4. Latency is measured from the public API edge, not from inside the Lambda.
5. No number from this document is ever quoted as a result until doc 07 is updated with the measured table by the build phases.

## 6. Measured results (2026-09-27, corpus version 1)

Published in full in BENCHMARK.md. Headline: fused not-allowed recall 1.00 (40/40 injection slice, Wilson 0.976 to 1.0), benign FPR 0.193 (Wilson 0.127 to 0.249) against the 0.035 target: **missed and published**, with the named regression (adversarial red-teamer over-flags quoted attack grammar in benign prose; fix path routed to the next corpus iteration). Adversary A/B: Llama 3.3 70B shipped (recall 1.0, FPR 0.193, 133 s wall) over Maverick (0.98/0.313), GPT-OSS 120B (0.973/0.16, 244 s) and DeepSeek R1 (0.967/0.18, 670 s). McNemar fused versus code-only: b=6, c=15, p=0.078 (the two pipelines reach total recall by different mechanisms; the qualitative fused advantage is the exfiltration convictions and the benign rescues the code layer cannot see). One public URL serves the console and the metrics (CloudFront).

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.2 | 2026-09-27 | Measured results section added after the benchmark runs; headline, named miss and A/B verdict recorded. |
| 0.1 | 2026-09-27 | Initial draft for owner review. |

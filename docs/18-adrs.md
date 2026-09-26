# Doc 18: Architecture Decision Records

Version 0.1 · Status: Draft · 2026-09-27

The six decisions that define Antares. Each: context, decision, alternatives rejected, consequences owned.

## ADR-001: The deterministic code gate holds veto power

**Context:** an LLM asked to validate schemas and regexes hallucinates, costs tokens, and adds latency to the most common case.
**Decision:** pure code (Pydantic, shell tokenizer, ARN allowlist, class weights) runs first and holds veto; models are invoked only on escalation. Models can block within their remit; they can never unblock a code veto.
**Rejected:** LLM-as-first-gate (the original cross-agent proposal); policy engines alone (no intent judgment, no radius).
**Consequence:** the fastest 75 percent of calls are model-free and free; the brand line "models propose, code decides" is enforced by control flow, not slogan.

## ADR-002: Cross-vendor adversarial quorum, default chosen by benchmark

**Context:** same-family models share lineage and blind spots; a quorum of one family is consensus theater.
**Decision:** blast-radius reasoning stays Amazon-native (Nova Pro); the red-team adversary is a non-Amazon family model, default Meta Llama 3.3 70B, with Llama 4 Maverick, GPT-OSS 120B and DeepSeek R1 A/B-tested on the doc 07 corpus. The benchmark table picks the shipped default.
**Rejected:** Nova-only role-orthogonal quorum (viable fallback, weaker decorrelation claim); majority-of-five quorums (latency and cost blow the budget for marginal signal).
**Consequence:** the decorrelation claim is empirical, published, and immune to the "isn't this just one vendor grading itself" question.

## ADR-003: Saga compensating rollbacks over snapshots

**Context:** VM snapshots and backup restores are slow, coarse, and prove nothing in a demo window.
**Decision:** pre-capture exact prior state to a TTL vault before any commit; reversal is a synthesized compensating transaction with byte-identity verification.
**Rejected:** snapshot-based recovery (minutes, not seconds, and invisible in a live demo); dry-run-only gating (no recourse when a mutation legitimately commits and later proves bad).
**Consequence:** reversibility becomes a system property; the demo can show a real mutation unhappen, which no screenshot competitor can match.

## ADR-004: The kernel lives in a sandbox namespace it cannot escape

**Context:** running destructive demos on the author's real account is a reviewer-facing landmine and a credibility trap.
**Decision:** all demo resources live in a dedicated namespace; kernel IAM carries Resource-scoped policies to exactly those ARNs; an out-of-scope mutation test runs in CI against a cloned role; `ANTARES_HALT` is the kill switch.
**Rejected:** "be careful" operating discipline (not a control); separate sandbox AWS account (better long-term, blocked by the single-account window reality, documented as enterprise-era work).
**Consequence:** the strongest security claim in the suite is testable in CI, and the doc 08 checklist turns posture into evidence.

## ADR-005: Three-state verdicts with a 60-second single-use bypass

**Context:** a kernel that hard-blocks ambiguous legitimate work gets uninstalled in a week; a kernel that allows everything is decoration.
**Decision:** ALLOW, HARD_BLOCK, ABSTAIN. ABSTAIN suspends the call with a KMS-signed, single-use, 60-second bypass token bound to the verdict; approval is ledgered; disagreement never averages, it escalates.
**Rejected:** two-state verdicts (no home for ambiguity); long-lived approval tokens (replay and theft surface).
**Consequence:** the anti-uninstall problem has a designed answer, and human-in-the-loop has a cryptographic audit trail.

## ADR-006: AWS-native serverless over containers

**Context:** the kernel must be live, cheap, and explainable within the window, and survive judge traffic bursts.
**Decision:** Lambda ARM64, API Gateway, DynamoDB single-table, EventBridge, S3/CloudFront, KMS, Secrets Manager, CloudWatch/X-Ray, CloudTrail; deploy via CloudFormation package/deploy of SAM templates.
**Rejected:** containers on App Runner/ECS (always-on cost, slower cold story for a gate); Graviton EC2 (operations burden with no benefit here); OpenSearch (per-hour cost trap for zero required capability).
**Consequence:** the cost model holds under 10 USD, the failure matrix is simple, and every service on the diagram has a stated reason, which is itself a judging criterion.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

## ADR-007: Naming, iteration one and two (SUPERSEDED by ADR-008)

**Context:** the original proposal branded the product "NovaKernel", inheriting Amazon's Nova model-line name. The vendor-agnostic architecture (ADR-002) made supplier branding a contradiction, the name collided with OpenStack Nova, and it muddied the builder's originality. An interim rename to "Governor" (the mechanical component that bounds runaway machines) was rejected by the owner as too plain for the intended register.
**Decision:** superseded. Rejected here: NovaKernel (supplier branding, OpenStack collision), Governor (correct concept, flat word), Interlock (machine-safety term, narrower than the full system), Arbiter (judgment-forward, undersells rollback and attestation).
**Consequence:** naming diligence continued in ADR-008, with each rejected name recorded so the search is never repeated.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

## ADR-007: The product is named Antares, not after any model line

**Context:** the original proposal branded the product "NovaKernel", inheriting Amazon's Nova model-line name. The defining architectural decision (ADR-002) is deliberately vendor-agnostic: Nova Pro judges blast radius, a non-Amazon family model red-teams it, and the benchmark picks the shipped adversary. Naming the product after one supplier's model line contradicts that decision, ages with that supplier's roadmap, and collides with OpenStack Nova, an existing infrastructure component. For a public project specifically, a supplier-branded name muddies the originality that belongs to the builder.
**Decision:** the product is named **Antares**, after the mechanical antares: the component that every machine capable of running away carries to bound its own energy. Watt's centrifugal antares is the founding icon of automatic control theory, and the one-line story writes itself: every machine that can run away has a antares; agents are machines that run away. The generic word "kernel" remains in prose as the component term; "Antares" is the product and brand.
**Alternatives rejected:** NovaKernel (supplier branding, OpenStack collision); Interlock (the machine-safety term, strong runner-up, slightly narrower than the full system); Arbiter (judgment-forward, undersells rollback and attestation).
**Consequence:** tagline fixed as "The execution antares for autonomous AI agents." The name survives any future change of models or vendors. CI keeps a grep gate: the string "NovaKernel" must never appear in docs or code again.

## ADR-008: The product is named Antares

**Context:** three names were evaluated and rejected (ADR-007): NovaKernel (supplier-model branding, OpenStack collision), Governor (founder veto: too plain), Regulus (conflict discovered by search: Regulus Cyber operates in autonomous-systems security, and a live REGULUS platform does AI compliance and validation, the exact semantic space; a reviewer or AI scorer searching the name would surface a competitor's description). The naming method followed the founders' pattern: Google named the magnitude of its mission (googol), Amazon named scale (the largest river), Anthropic named its worldview (the anthropic principle), Amazon's own line names geology and cosmos (Bedrock, Nova, Titan, Aurora).
**Decision:** the product is named **Antares**. Antares is the red supergiant at the heart of the Scorpion, the brightest star of the summer sky, and its name literally means "rival of Ares", the star that outshines the god of war. It is also one of the four Royal Stars of Persia, the Watchers of the Sky, assigned to watch the west. For a strictly defense-only execution kernel that watches every agent action and stands against hostile behavior, the name encodes the mandate in the sky. The crimson star gives the console its signal color and the verdict its red.
**Alternatives rejected:** NovaKernel, Governor, Regulus, Interlock, Arbiter (recorded in ADR-007); Astraea (strong rollback myth, harder spelling); Themis (elegant, but an active AI-evaluation company operates under the name); Maat (reads "Matt"); Argus (names only the watching layer); Janus (two-faced is a trust insult for a trust product).
**Consequence:** tagline fixed as "Antares: the execution governor for autonomous AI agents." Repo: `antares`. CLI: `antares gate`, `antares probe`, `antares rollback`. Events: `antares.decision`, `antares.incident`. Sandbox resources: `antares-demo-ledger`, `antares-demo-vault-846719`, `/antares/demo/*`, kill switch `ANTARES_HALT`. Brand note: if the project incorporates, trademark counsel re-checks class 9 and 42 (an audio-software company holds an Antares mark in music); the standard founder path of codename now, brand later applies, exactly BackRub to Google and Bard to Gemini.

| 0.3 | 2026-09-27 | Added ADR-008: final name Antares, full naming record with all rejected candidates. |

# Antares: Documentation Suite

> The deterministic execution kernel for autonomous AI agents on AWS. Every tool call an agent attempts is gated by code first, judged by a cross-vendor model quorum second, measured against live cloud state, and reversible by construction. Models propose, code decides.

**Antares: the execution antares for autonomous AI agents.** Every machine that can run away carries a antares; agents are machines that run away.

Version 0.2 · Status: Draft, full suite awaiting owner review · Owner: Prakhar Shukla · 2026-09-27

## Document Index

| # | Document | What it answers |
|---|----------|-----------------|
| 01 | [Vision](docs/01-vision.md) | Problem, why now, landscape, open-core business model |
| 02 | [PR/FAQ](docs/02-prfaq.md) | Amazon working-backwards gate: launch-day press release and hard questions |
| 03 | [Product Spec](docs/03-product-spec.md) | Personas, journeys, features F1 to F8, acceptance criteria, scope cuts |
| 04 | [Architecture](docs/04-architecture.md) | Subsystems S0 to S7, request paths, AWS service map, failure matrix |
| 05 | [Agent Contracts](docs/05-agent-contracts.md) | The enforcement surface: schemas every agent and tool must satisfy |
| 06 | [Data Design](docs/06-data-design.md) | Single-table layout, state vault, Merkle chain, evidence storage |
| 07 | [Evaluation](docs/07-evaluation.md) | 300-case corpus, metric bars, adversary A/B protocol, honesty rules |
| 08 | [Security and Privacy](docs/08-security-privacy.md) | Threat model for the kernel itself, sandbox namespace, launch checklist |
| 09 | [Deployment](docs/09-deployment.md) | Environments, deploy mechanics, cost model, availability-gate strategy |
| 10 | [Console](docs/10-console.md) | Public zero-login surface, screens, interaction spec, design language status |
| 11 | [Roadmap](docs/11-roadmap.md) | Launch phases P0 to P6, eras beyond, what is cut and why |
| 12 | [Pitch](docs/12-pitch.md) | Video script skeleton, launch checklist, proof pack plan |
| 13 | [API Spec](docs/13-api-spec.md) | REST contract, error registry, EventBridge event schemas |
| 14 | [Testing Strategy](docs/14-testing-strategy.md) | Test pyramid, phase loop, CI gates, definition of done |
| 15 | [Risk Register](docs/15-risk-register.md) | Scored risks with mitigations and early warnings |
| 16 | [Glossary](docs/16-glossary.md) | Normative definitions of every term |
| 17 | [Non-Functional and SLOs](docs/17-nonfunctional-slo.md) | Latency budgets, availability, error budget policy, data classification |
| 18 | [ADRs](docs/18-adrs.md) | The eight decisions that define the system |
| 19 | [Tech Stack](docs/19-tech-stack.md) | The current and latest stack, pinning policy, rejected options |
| -- | [What Broke](docs/what-broke.md) | Real-time failure ledger, appended during build, never edited retroactively |

## One-Paragraph Summary

Enterprises are handing autonomous agents privileged cloud access, and a single hallucinated or injected tool call can destroy production state with no recourse. Text-level guardrails only read strings, static scanners only read code, and posture tools only watch configuration; nothing governs the moment an agent's decision becomes a live AWS mutation. **Antares** is that missing layer: an in-line hypervisor that intercepts every mutating tool call, enforces a deterministic code gate with veto power, obtains adversarial cross-vendor consensus (Amazon Nova Pro judging blast radius, a non-Amazon family model red-teaming intent), measures real blast radius from live read-only probes of actual AWS state, executes through compensating sagas that make every mutation reversible, and writes a tamper-evident Merkle receipt for every action. It ships with a zero-login public console where anyone can dispatch preset scenarios against live sandboxed AWS resources and watch the kernel vote, block, and roll back in real time.

## Build Limitations (read before judging)

Nothing is built yet as of this version. Every number in this suite is a design target until the benchmarks of doc 07 are run and back-filled with dated, measured values. Specifics:

- **Latency figures** in docs 04, 13 and 17 are budgets and targets, not measurements.
- **Detection metrics** in doc 07 are targets on a designed corpus, not observed field performance.
- **Multi-account governance** (Control Tower, cross-org roles) is documented as the enterprise tier and deliberately out of scope for the build window.
- **Mutation surface** is limited to the sandbox namespace: one DynamoDB table, one S3 bucket, one SSM path prefix. The kernel's IAM role can touch nothing else, by policy and by proof (doc 08).

## Design Principles (non-negotiable)

1. **Code decides.** The deterministic gate holds veto. No model, anywhere in the pipeline, can overturn a code-level BLOCK or force an action past policy.
2. **Evidence or it did not happen.** Every verdict, vote and mutation carries a receipt. A security decision without an audit trail is a rumor.
3. **Blast radius is measured, never imagined.** Radius comes from live read-only probes of real AWS state, not from a model's imagination.
4. **Every mutation is reversible.** Actions run through compensating sagas with pre-captured state, or they wait.
5. **The kernel cannot harm what it guards.** Its IAM scope ends at the sandbox namespace. A safety product that can nuke its own account is a landmine, not a product.
6. **Honest metrics.** Measured numbers only, corpus and thresholds disclosed, Wilson 95 percent intervals on every proportion.
7. **Fail open or fail loud, by policy, never by accident.** Reads degrade to allow-with-flag when the kernel is down; destructive classes halt. The failure behavior is itself a documented, tested policy.

## Conventions

- Diagrams: Mermaid, rendered natively on GitHub.
- Errors: RFC 7807 problem+json (doc 13).
- Proportions: Wilson 95 percent intervals (doc 07).
- Commits: conventional commits. No em dashes anywhere, in code, docs, or commit messages.
- Doc statuses: Draft, then Reviewed, then Locked. Only Locked docs gate build phases.
- Failure ledger: every build failure lands in what-broke.md the day it happens, with symptom, root cause, fix, prevention, phase. Entries are append-only.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial full suite drafted for owner review. No doc is Locked. |

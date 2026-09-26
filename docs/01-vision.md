# Doc 01: Vision

Version 0.1 · Status: Draft · 2026-09-27

## The problem

Autonomous AI agents are being granted privileged cloud access: coding agents that provision, DevOps agents that remediate, operations agents that mutate. Every one of those agents turns a language model's output into live API calls against real infrastructure. The failure modes are new and unguarded:

- **Tool hallucination:** the model invents a plausible call with plausible parameters against the wrong resource.
- **Injected tool calls:** untrusted content the agent read earlier (logs, issues, documents) carries instructions that surface as tool arguments. Prompt injection is risk LLM01 in the OWASP Top 10 for LLM Applications.
- **Runaway blast radius:** the agent did technically what was asked, and what was asked destroys more than anyone priced in.
- **Zero recourse:** after a destructive call commits, recovery is manual, slow, and often impossible.

## Why now

Two curves crossed. Agent deployments moved from demos to production duties, and the models driving them got good enough to be trusted with real credentials. The governance layer did not move with them. This hackathon (2,593 registered builders invited to connect coding agents to AWS) is a compressed preview of the next two years of enterprise reality.

## The landscape, and the gap

| Layer | Examples | What it sees | What it misses |
|---|---|---|---|
| Text guardrails | Bedrock Guardrails, Lakera, Aporia | The content string | Tool parameters, shell metacharacters, live cloud state |
| Static analysis | Checkov, Trivy, Snyk | IaC files before deploy | Runtime agentic decisions entirely |
| Cloud posture | CSPM tools, config auditors | Configuration drift | The moment of mutation, the acting agent |
| **Runtime execution layer** | **nobody mainstream** | **the mutation itself, in-flight** | (this is the gap Antares occupies) |

The claim is deliberately narrow: the unoccupied layer is the runtime execution choke point. Not "AI security" broadly; one layer, owned completely.

## Business model: open-core

Following the Terraform and HashiCorp playbook:

- **Open core (Apache 2.0):** the kernel gateway, deterministic gate, probe library, saga engine, console. Drives adoption, scrutiny and trust. Security infrastructure nobody can inspect is security infrastructure nobody deploys.
- **Enterprise (paid):** multi-account Control Tower governance, org-wide policy packs, RBAC with identity-provider integration, compliance audit exports, cross-region recovery for agentic mutations.
- **Pricing shape:** free developer tier (bounded gated actions per month), per-seat team tier, per-gated-action enterprise pricing with a platform fee. Exact figures are a launch decision, not a doc-01 promise.

Market sizing language discipline: analyst projections consistently put agent-security and AI-governance spending in the billions of dollars by 2028. No precise invented figure is claimed anywhere in this suite.

## Why this builder

The author's shipped work is a single research arc about decisions that must not be wrong: TruthLayer (calibrated verification of AI claims), Sentinel (deterministic fraud scoring with evidence bundles), Gatehouse (an agent that gates scam decisions with hash-chained evidence). Antares is the same discipline pointed at the infrastructure layer: models propose, code decides.

## Vision risks

Named honestly, scored in doc 15: the demo must land in seconds or the depth is invisible; latency budgets must hold or inline gating is unusable; the kernel itself must be un-hackable or it becomes the attack surface; and the category must stay empty long enough to establish the reference implementation.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

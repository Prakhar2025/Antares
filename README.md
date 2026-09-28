<p align="center">
  <img src="docs/media/antares-cover-1200x675.jpg" alt="Antares: a poisoned write judged live by the kernel" width="820">
</p>

<p align="center">
  <strong>The deterministic execution governor for autonomous AI agents on AWS.</strong><br>
  Every mutating tool call is gated by deterministic code first, judged on escalation by a<br>
  cross-vendor Amazon Bedrock quorum, measured against live cloud state, reversible by construction.
</p>

<p align="center">
  <img alt="CI" src="https://github.com/Prakhar2025/Antares/actions/workflows/ci.yml/badge.svg">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="Bedrock" src="https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazonaws&logoColor=white">
  <img alt="Console" src="https://img.shields.io/badge/console-Next.js-000000?logo=nextdotjs&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-4cc38a">
</p>

<p align="center">
  <a href="docs/media/antares-walkthrough-103s.mp4"><img alt="Walkthrough" src="https://img.shields.io/badge/%E2%96%B6%20walkthrough-103%20seconds-FF0000?logo=youtube&logoColor=white"></a>
  <a href="https://d3jhd66xz9xdo9.cloudfront.net"><img alt="Live console" src="https://img.shields.io/badge/live%20console-attack%20it%20yourself-4cc38a"></a>
</p>

<p align="center">
  <a href="docs/media/antares-walkthrough-103s.mp4"><strong>Watch the 103-second walkthrough</strong></a>
  &nbsp;&middot;&nbsp;
  <a href="https://d3jhd66xz9xdo9.cloudfront.net"><strong>Live console, zero login</strong></a>
  &nbsp;&middot;&nbsp;
  <a href="BENCHMARK.md">Benchmark</a>
  &nbsp;&middot;&nbsp;
  <a href="docs/what-broke.md">Failure ledger</a>
</p>

<p align="center">
  <a href="docs/media/antares-walkthrough-103s.mp4"><img src="docs/media/antares-cover-1200x675.jpg" alt="Antares: the poisoned write, judged live" width="620"></a>
</p>

---

Agents hold real credentials. Antares stands between their decisions and your
cloud: every mutating tool call is gated by deterministic code first, judged on
escalation by a cross-vendor Amazon Bedrock quorum, measured for blast radius
against live cloud state through read-only probes, executed through compensating
sagas, and recorded into a tamper-evident Merkle chain. The principle is also
the control flow: **models propose, code decides.**

**Status: live on AWS, zero login, USD 10 budget alarm, under USD 2 spent.**

## Live, zero login

The public site serves the real kernel through the same URL: open the console,
pick a scenario, dispatch, and watch the verdict stream carry real Bedrock
votes, live blast-radius probes and a receipt.

- Site: https://d3jhd66xz9xdo9.cloudfront.net
- Console: https://d3jhd66xz9xdo9.cloudfront.net/console

![Antares console](docs/assets/console.png)

Nothing in the console is mocked. The poisoned write you can dispatch carries
OWASP LLM01 in a data field; the perimeter flags it before any model runs; both
model families vote in parallel; the fused verdict hard-blocks and the evidence
bundle is persisted.

## Why this exists

| Existing layer | What it reads | What it cannot see |
|---|---|---|
| Text guardrails | content strings | tool parameters, shell metacharacters, resource ARNs, live state |
| Static analysis (IaC scanners) | code, before deploy | runtime agentic decisions |
| Cloud posture management | configuration drift | the moment a mutation executes |

The runtime execution choke point, the exact moment an agent's thought becomes
a live AWS mutation, was unoccupied. Antares occupies it.

## How a call is judged

Six stages. Four of them can kill the call.

| Stage | Subsystem | Guarantee |
|---|---|---|
| 01 | Perimeter (S0) | untrusted content is canonicalized, then screened by a 16-rule signature library and a semantic classifier; findings travel as identifiers, hostile text never reaches a model raw |
| 02 | Deterministic gate (S2) | pure code with final veto: schemas, shell tokens, ARN allowlists, class weights |
| 03 | Cross-vendor quorum (S3) | escalated calls argued twice in parallel by families with no shared lineage; adversary conviction blocks, divergence forces a human |
| 04 | State probes (S4) | blast radius measured from live AWS state; a failed probe means maximum severity |
| 05 | Human signature (S5) | destructive classes always abstain, even with clean votes; approvals are KMS-signed, single-use, dead in 60 seconds |
| 06 | Provenance ledger (S6) | every verdict hashed into a Merkle chain; receipts verify client-side |

Fusion is a deterministic decision table, not an average:

| Condition, in order | Verdict | Fusion id |
|---|---|---|
| A model echoed the planted canary audit reference | HARD_BLOCK | QUORUM-TRIP-001 |
| Adversary risk ≥ block threshold, class not READ | HARD_BLOCK | QUORUM-BLK-001 |
| Either vote missing or unparseable | ABSTAIN | QUORUM-VOTE-001 |
| Divergence ≥ abstain threshold | ABSTAIN | QUORUM-DIV-001 |
| Reasoner blast risk ≥ abstain threshold | ABSTAIN | QUORUM-BLAST-001 |
| Destructive class, approval policy on | ABSTAIN | QUORUM-DEST-001 |
| Otherwise | ALLOW | QUORUM-ALLOW-001 |

## Measured, including the miss

On the published, versioned 300-case corpus (150 benign, including 44
adversarial-benign; 150 adversarial across six classes), measured 2026-09-27
against the live stack with real Bedrock votes:

| Result | Value | Target |
|---|---|---|
| Not-allowed recall on attacks (fused) | 1.000 (Wilson 95 percent: 0.976 to 1.0) | 1.0 |
| Injection-driven-mutation slice | 40/40 | all |
| Benign false-positive rate | 0.193 (Wilson: 0.127 to 0.249) | 0.035, **missed and published** |
| Fast-path latency | 22 to 34 ms | 250 ms |
| Escalated latency | 596 to 940 ms | 3.5 s |

The red-team seat itself was decided by this table: four candidates ran the
full corpus with identical prompts and thresholds, and Llama 3.3 70B shipped on
total recall at the best wall time (133 s), ahead of Llama 4 Maverick (noisy,
FPR 0.313), GPT-OSS 120B (conservative, recall 0.973) and DeepSeek R1 (5x
slower for no gain).

Every number is scoped to this corpus: a designed, versioned corpus, not field
performance across the unbounded space of real traffic. The full methodology,
Wilson intervals, the McNemar comparison against the code-only baseline
(b = 6, c = 15, p = 0.078, published with the discordant-pair counts) and the
named regression behind the FPR miss are in [BENCHMARK.md](BENCHMARK.md).

![Antares benchmark](docs/assets/benchmark.png)

## API surface

Eleven routes. Eight are public and edge-throttled (10 requests per second,
burst 20); the mutation routes require an API key.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/gate` | public | judge a tool call: perimeter, gate, quorum, probes, verdict + receipt |
| POST | `/v1/screen` | public | perimeter-only content screen |
| POST | `/v1/canaries` | public | canary audit-reference registry |
| POST | `/v1/tripwire/check` | public | over-compliance tripwire check |
| GET | `/v1/incidents` | public | incident records |
| GET | `/v1/metrics` | public | live decision counters |
| GET | `/v1/attacks` | public | recorded attack replays |
| GET | `/v1/decisions/{id}` | public | fetch a stored verdict by id |
| POST | `/v1/execute` | API key | execute an approved mutation through the saga |
| POST | `/v1/actions/{id}/rollback` | API key | reverse an executed action from the vault |
| GET | `/v1/actions/{id}/receipt` | API key | fetch the Merkle receipt for an action |

Errors are RFC 7807 problem+json (doc 13).

## Security model

- The kernel's IAM reach ends at three sandbox resources, verified by a
  CI-gated out-of-scope mutation test.
- Kill switch: one environment flag returns 503 kernel-halted from every gate;
  exercised live through the public URL.
- Human approvals: KMS-signed, single-use, dead in 60 seconds, ledgered on
  redemption.
- A live USD 10 monthly cost budget alarms the account; competition-window
  spend is under USD 2. ARM64 compute, on-demand DynamoDB, free-tier
  CloudFront: no always-on burn.

## Built by an agent, provably

The project was built end to end by a coding agent connected to AWS, reviewed
at every milestone gate. CloudTrail records the agent's own build calls,
committed as a proof pack with its generation script
([docs/submission/proof-pack.json](docs/submission/proof-pack.json)). The
failure ledger ([docs/what-broke.md](docs/what-broke.md)) carries every build
failure the day it happened with root cause and prevention rule, seventeen
entries at this writing; a failure without a prevention rule is treated as
unfixed.

## Design principles

1. **Code decides.** No model anywhere in the pipeline can overturn a code
   rejection.
2. **Evidence or it did not happen.** Every verdict, vote and mutation carries
   a receipt.
3. **Blast radius is measured, never imagined.**
4. **Every mutation is reversible**, or it waits.
5. **The kernel cannot harm what it guards.** Its IAM scope ends at the sandbox.
6. **Honest metrics.** Measured numbers only, corpus and thresholds disclosed,
   Wilson 95 percent intervals on every proportion.
7. **Fail open or fail loud, by policy, never by accident.**

## Documentation

| # | Document | What it answers |
|---|---|---|
| 01 | [Vision](docs/01-vision.md) | problem, why now, landscape, open-core model |
| 02 | [PR/FAQ](docs/02-prfaq.md) | Amazon working-backwards gate |
| 03 | [Product Spec](docs/03-product-spec.md) | personas, journeys, features F1 to F8 |
| 04 | [Architecture](docs/04-architecture.md) | subsystems, request paths, failure matrix |
| 05 | [Agent Contracts](docs/05-agent-contracts.md) | the enforcement surface: schemas |
| 06 | [Data Design](docs/06-data-design.md) | single-table layout, vault, Merkle chain |
| 07 | [Evaluation](docs/07-evaluation.md) | corpus, metric bars, A/B protocol |
| 08 | [Security and Privacy](docs/08-security-privacy.md) | threat model for the kernel itself |
| 09 | [Deployment](docs/09-deployment.md) | environments, deploy mechanics, cost model |
| 10 | [Console](docs/10-console.md) | public zero-login surface |
| 11 | [Roadmap](docs/11-roadmap.md) | phases P0 to P6, eras beyond |
| 12 | [Pitch](docs/12-pitch.md) | video script, launch checklist |
| 13 | [API Spec](docs/13-api-spec.md) | REST contract, error registry, events |
| 14 | [Testing Strategy](docs/14-testing-strategy.md) | test pyramid, phase loop, CI gates |
| 15 | [Risk Register](docs/15-risk-register.md) | scored risks with mitigations |
| 16 | [Glossary](docs/16-glossary.md) | normative definitions |
| 17 | [Non-Functional and SLOs](docs/17-nonfunctional-slo.md) | latency budgets, error budget policy |
| 18 | [ADRs](docs/18-adrs.md) | the eight decisions that define the system |
| 19 | [Tech Stack](docs/19-tech-stack.md) | current stack, pinning policy, rejected options |
| -- | [What Broke](docs/what-broke.md) | append-only failure ledger |
| -- | [Submission article](docs/submission/technical-article-v2.md) | the long-form engineering write-up |

## Run your own stack

Requirements: AWS CLI configured, AWS SAM CLI, Python 3.12, Node 20, GNU make.

```
make deploy      # builds the aarch64 bundle and deploys the dev stack
make verify      # receipt verification against a live decision
make test        # unit + contract suites
make lint        # ruff + mypy strict
make eval        # the doc 07 benchmark harness
```

The deploy creates only the sandbox namespace: two DynamoDB tables, the site
bucket, the Lambda functions, the regional API and the CloudFront
distribution. Console source lives in [console/](console); it is a Next.js
static export served from S3 with `/v1/*` proxied same-origin to the API.

## License

Apache License 2.0.

## Author

**Prakhar Shukla** builds fraud-defense and AI-trust infrastructure from
Nagpur, India. TruthLayer verifies what AI claims. Gatehouse gates scam
decisions. Sentinel scores cross-merchant fraud. Antares governs the agents
themselves. Two IEEE publications on deepfake detection; national winner at
IIT Delhi; top 50 global finalist in the AWS AIideas competition.

# Judging agent tool calls before they execute: the Antares kernel

*Prakhar Shukla · built end to end with a coding agent connected to AWS · September 2026 · corpus v1*

**Abstract.** Autonomous agents hold real cloud credentials, and the industry's
defenses screen text, not executions. Antares is a deterministic execution
kernel that intercepts every mutating tool call an agent attempts, vetoes it
with pure code where code can decide, escalates what code cannot decide to a
cross-vendor model quorum on Amazon Bedrock, measures blast radius from live
cloud state through read-only probes, executes through compensating sagas, and
issues a verifiable Merkle receipt per verdict. On a published, versioned
300-case corpus the fused pipeline reached not-allowed recall of 1.000 on
attacks (Wilson 95 percent: 0.976 to 1.0) with a fast path of 22 to 34 ms
against a 250 ms budget, and it published a miss: a benign false-positive rate
of 0.193 against a 0.035 target, with the regression named and the fix path
scheduled. Every claim in this article is reproducible from the repository:
nineteen versioned design documents, a seventeen-entry failure ledger, a
CloudTrail proof pack of the agent's own build calls, and the benchmark corpus
itself.

---

## 1. The gap: nothing governs the moment a decision becomes a call

An agent's loop is simple: the model emits a tool call, the harness executes it
against real infrastructure. Every capability that makes agents useful, reading
tickets, mutating databases, deploying code, paging humans, arrives through
that one pipe. Three existing layers each cover a different slice of the
problem, and none of them covers the pipe:

| Layer | What it reads | What it cannot see |
|---|---|---|
| Text guardrails (Bedrock Guardrails, Lakera and peers) | content strings | tool parameters, shell metacharacters inside an UpdateExpression, resource ARNs, live cloud state |
| Static analysis (Checkov, Trivy, Snyk) | infrastructure-as-code, before deploy | runtime agentic decisions, which do not exist at scan time |
| Cloud posture management | configuration drift | the moment a mutation executes |

The runtime execution choke point was unoccupied. Antares occupies it.

The threat is not hypothetical. Prompt injection ranks first in the OWASP Top
10 for LLM applications: untrusted text carrying hidden instructions hijacks
the agent that reads it, and an agent with credentials turns that hijack into
API calls. A single hallucinated or injected mutation can destroy state that
took months to build; recovery without a pre-captured prior image is
archaeology.

## 2. What Antares is

Antares is the deterministic execution kernel for autonomous AI agents on AWS.
Agents submit tool calls; the kernel gates them with code first, judges
escalated calls with a cross-vendor Bedrock quorum, measures blast radius from
live read-only probes, executes through compensating sagas, and issues Merkle
receipts. The principle is also the control flow: **models propose, code
decides.** No model anywhere in the pipeline can overturn a code rejection, and
a code block short-circuits all model invocations.

## 3. Architecture: seven subsystems

| Stage | Input | Output | Guarantee |
|---|---|---|---|
| S0 Perimeter | untrusted content in parameters | finding identifiers | hostile text never reaches a model raw |
| S1 Kernel gateway | agent tool call | routed dispatch | unregistered tools 404; registered tools carry strict Pydantic schemas |
| S2 Deterministic gate | validated call | allow, or veto with rule ids | pure code, microsecond latency, final veto |
| S3 Cross-vendor quorum | escalated call | two votes, fused verdict | adversary conviction blocks; divergence forces a human |
| S4 State probes | proposed mutation | blast radius score | measured from live state; failed probe means maximum severity |
| S5 Saga engine | approved mutation | commit or rollback | prior state captured before commit; restoration verified by hash |
| S6 Provenance ledger | every verdict | Merkle receipt | head advances by conditional write; receipts verify client-side |

**S0 Perimeter.** Untrusted content is canonicalized before any consumer trusts
it: homoglyph folding (Cyrillic і for Latin i), invisible-character stripping,
HTML entity decoding, base64 channel decoding. A 16-rule signature library then
matches the canonical text, and a semantic classifier (Nova Lite) scores
residual risk. Findings travel forward as identifiers; raw hostile text never
reaches a model.

**S1 Kernel gateway.** The only path from agent to AWS. Unregistered tools
return 404; registered tools carry strict Pydantic schemas. The gateway is also
where the kill switch lives: one environment flag turns every gate response
into 503 kernel-halted.

**S2 Deterministic gate (ADR-001).** Pure code: schema validation, shell
metacharacter tokenization, ARN allowlists scoped to the sandbox namespace,
per-class severity weights. It runs in single-digit milliseconds at zero token
cost, and its veto is final.

**S3 Cross-vendor quorum (ADR-002).** Escalated calls, destructive or
permission classes, are judged twice in parallel: Amazon Nova Pro reasons blast
radius and intent alignment, and a model from a different training lineage, the
benchmark shipped Meta Llama 3.3 70B, assumes the call is an attack and hunts
for one. Fusion is a deterministic decision table, not an average; see section
4.

**S4 State probes and blast radius.** The radius score comes from live
read-only Describe and List calls: item existence, table counts, point-in-time
recovery status, S3 versioning. Score = resource count × severity weight ×
(1 − reversibility). If a probe fails, the radius is marked unknown and the
call is treated at maximum severity. No model estimates blast radius.

**S5 Saga engine.** Before any mutation commits, the exact prior state is
captured into a one-hour TTL vault. Rollback replays the inverse operation and
verifies restoration by hash. Reversibility is a system property, not an
emergency response.

**S6 Provenance ledger.** Every record is hashed into a Merkle chain whose head
advances by conditional write, so tampering forks the chain visibly. Receipts
verify client-side: hash the canonical record, compare the leaf.

## 4. The fusion decision table

The quorum's output is decided by a fixed table evaluated in order. There is no
averaging anywhere in it.

| Condition (evaluated in order) | Verdict | Fusion id |
|---|---|---|
| A model echoed the canary audit reference | HARD_BLOCK | QUORUM-TRIP-001 |
| Adversary risk ≥ block threshold and class is not READ | HARD_BLOCK | QUORUM-BLK-001 |
| Either vote missing or unparseable | ABSTAIN | QUORUM-VOTE-001 |
| Divergence ≥ abstain threshold | ABSTAIN | QUORUM-DIV-001 |
| Reasoner blast risk ≥ abstain threshold | ABSTAIN | QUORUM-BLAST-001 |
| Destructive class, policy requires approval | ABSTAIN | QUORUM-DEST-001 |
| Otherwise | ALLOW | QUORUM-ALLOW-001 |

Two properties of this table carry the security argument. First, the adversary
is biased: its system prompt instructs it to assume the call is an attack, so
its conviction alone blocks, while the reasoner alone can only force a human
decision, never an approval. Second, the last row is unreachable for destructive
classes: even a unanimous clean vote abstains to a human signature, delivered as
a KMS-signed, single-use bypass token dead in 60 seconds and ledgered on
redemption.

The canary tripwire defends the quorum itself. Every quorum prompt carries a
planted audit reference in its data section; policy instructs the models never
to repeat it. A model that repeats it has obeyed data over policy, which is
exactly the failure mode a jailbroken model exhibits, so the echo itself is a
conviction.

## 5. Why the adversary is cross-vendor, and how the seat was decided

Same-family models share pretraining lineage and, with it, correlated blind
spots. A red-teamer from the same family as the reasoner is consensus theater.
Four candidates ran the full 300-case corpus with identical prompts and
thresholds; the table picked the shipped default on recall first,
false-positive rate second, wall time third:

| Adversary | Not-allowed recall | Hard-block recall | Benign FPR | Wall (300 cases) |
|---|---|---|---|---|
| **Meta Llama 3.3 70B (shipped)** | **1.000** | 0.700 | 0.193 | 133 s |
| Meta Llama 4 Maverick | 0.980 | 0.680 | 0.313 | 123 s |
| OpenAI GPT-OSS 120B | 0.973 | 0.647 | **0.160** | 244 s |
| DeepSeek R1 | 0.967 | 0.647 | 0.180 | 670 s |

Llama 3.3 70B shipped on total recall at the best wall time; Maverick was the
fastest but the noisiest on benign traffic (FPR 0.313); GPT-OSS was the most
conservative and missed attacks (recall 0.973); DeepSeek R1 was five times
slower for no accuracy gain. The full comparison, with Wilson intervals and the
methodology, is in the repository's BENCHMARK.md.

This is also a Bedrock story. Amazon Bedrock is the only platform where a
cross-vendor security quorum, Amazon judging, Meta attacking, the market
deciding, is even possible in one API.

## 6. What the benchmark measured, including the miss

The corpus is public and versioned (v1): 150 benign operational cases,
including 44 adversarial-benign (quoted attack grammar inside benign security
prose), and 150 adversarial across six named classes. Every number below ran
against the live stack with real Bedrock votes, measured 2026-09-27,
us-east-1.

| Result | Value | Target | Verdict |
|---|---|---|---|
| Not-allowed recall on attacks (fused) | 1.000 (Wilson: 0.976 to 1.0) | 1.0 | met |
| Injection-driven-mutation slice | 40/40 | all | met |
| Hard-block recall | 0.700 | design metric | published |
| Benign FPR | 0.193 (Wilson: 0.127 to 0.249) | 0.035 | **missed, published** |
| Fast-path latency | 22 to 34 ms | 250 ms | met |
| Escalated latency | 596 to 940 ms | 3.5 s | met |

The benign FPR miss is the most interesting number in the table. The misses
concentrate in the adversarial-benign slice: the red-teamer's persona
instructs it to assume malice, so it over-flags quoted attack grammar inside
benign security prose. The regression is named, the fix path is scheduled, and
the corpus is versioned so the next run is comparable. A benchmark that only
publishes wins is marketing.

McNemar's test on the fused pipeline versus the code-only baseline: b = 6,
c = 15, p = 0.078. Both pipelines reach total recall on this corpus by
different mechanisms; the honest reading is published rather than claimed as
significant. The qualitative difference is stated with the discordant-pair
counts: the code gate abstains honestly on everything destructive, while the
fused pipeline actively convicts the exfiltration cases code cannot see.

What is not proven: field performance beyond this designed corpus, and
behavior against adaptive attackers who know the defense. The corpus is
versioned and public; extend it and publish your numbers next to ours.

## 7. Three failures that shaped the system

**The account hook that rejects standard resources.** The development account
runs a CloudFormation early-validation hook that rejects
AWS::DynamoDB::GlobalSecondaryIndexes and AWS::CloudFront::OriginAccessControl
outright. Both are documented, standard resources. The fix was not a retry: the
data layer was redesigned to a single-table dual-write pattern (a lookup item
keyed by verdict id plus a state feed item, no indexes), and the site bucket
moved to a read-only public policy behind CloudFront. Both were bisected
through probe stacks and recorded in the failure ledger.

**Transactions that cannot contain the same key twice.** The execute marker,
the bypass redemption and the ledger head advance each originally paired a
ConditionCheck with a Put or Update on the identical item key. DynamoDB
forbids this. The fix: single-item conditional writes. The execute marker and
the ledger head are one conditional put each, and single-use bypass enforcement
lives on the verdict item itself. Three flows, one rule, applied consistently.

**Fakes that are looser than the real service.** The unit-test fake for
DynamoDB accepted plain integer ADD values and untyped items; real DynamoDB
requires typed values ({"N": "1"}). Unit tests stayed green while the live
stack failed twice. The fix tightened the fakes to mirror the real contract,
and the live smoke test became a hard gate after every deploy.

Each failure is in the repository's what-broke ledger (17 entries at this
writing) with its prevention rule. A failure without a prevention rule is
treated as unfixed.

## 8. Security model

- **Namespace.** The kernel's IAM reach ends at three sandbox resources,
  verified by a CI-gated out-of-scope mutation test.
- **Kill switch.** One environment flag; exercised live through the public URL
  (503 kernel-halted, then restored).
- **Human approvals.** KMS-signed, single-use, dead in 60 seconds, ledgered on
  redemption.
- **Public surface.** The zero-login console dispatches four preset scenarios
  through the same gate judges use; the public API stage is throttled to 10
  requests per second (burst 20); destructive routes (execute, rollback)
  require an API key and are not exposed on the public console.
- **Budget.** A live USD 10 monthly cost budget alarms the account; spend for
  the full competition window is under USD 2. The sandbox runs ARM64,
  on-demand DynamoDB and free-tier CloudFront: no always-on compute.

## 9. Build provenance: the agent that built it

The project was built end to end by a coding agent connected to AWS, with the
owner reviewing at every milestone gate. The evidence is objective, not
narrative: CloudTrail records the agent's own API calls across the build
window (Bedrock Converse invocations, Lambda deployments, DynamoDB operations),
committed as a proof pack with its generation script; nineteen design documents
with statuses and changelogs precede the code they gate; the what-broke ledger
records every failure the day it happened, with root cause and prevention.

## 10. What comes next

The FPR regression fix path is scheduled: a calibrated benign-persona prompt
for the adversary seat and a reweight of the adversarial-benign slice, measured
against corpus v1 so the delta is honest. After that: an adaptive-adversary
corpus extension (attacks that know the defense), multi-region replay of the
drills, and the bypass-token UX for human approvers.

## Pointers

- GitHub: github.com/Prakhar2025/Antares
- Live console: no login, dispatch a poisoned write, watch the quorum vote
- Benchmark: BENCHMARK.md in the repository, measured tables with dates and corpus version
- Failure ledger: docs/what-broke.md, every failure with its prevention rule
- Proof pack: docs/submission/proof-pack.json with its generation script

**Prakhar Shukla** builds fraud-defense and AI-trust infrastructure from
Nagpur, India. TruthLayer verifies what AI claims. Gatehouse gates scam
decisions. Sentinel scores cross-merchant fraud. Antares governs the agents
themselves. Two IEEE publications on deepfake detection; national winner at
IIT Delhi; top 50 global finalist in the AWS AIideas competition.

*Models propose, code decides.*

# Antares: gating autonomous AI agents with deterministic code, a cross-vendor quorum, and reversible execution

*Prakhar Shukla · built end to end with a coding agent connected to AWS · September 2026*

---

Autonomous agents now hold real cloud credentials. They read tickets, mutate
databases, deploy code and page on-call engineers. Every one of those
capabilities arrives through the same pipe: a language model emits a tool
call, and the call executes against production infrastructure.

Between the model's decision and the API call sits nothing.

This is the gap Antares fills. It is an execution governor: a kernel that
intercepts every mutating tool call an agent attempts, gates it with
deterministic code that holds veto power, judges escalated calls with a
cross-vendor model quorum running on Amazon Bedrock, measures blast radius
against live cloud state through read-only probes, executes through
compensating sagas, and records a tamper-evident Merkle receipt. The tagline
is also the architecture: models propose, code decides.

## Why text guardrails are not enough

The industry's default answer to agent safety is a guardrail on the model's
text. That is necessary and insufficient. A guardrail reads the content
string; it cannot see the tool parameters, the shell metacharacters inside
an UpdateExpression, the resource ARN pointing at a table outside the
namespace, or the live state that a deletion would destroy.

Three existing layers each cover one slice:

- **Text guardrails** (Bedrock Guardrails, Lakera and peers) screen content
  strings. They are blind to tool parameters and to cloud state.
- **Static analysis** (Checkov, Trivy, Snyk) scans infrastructure-as-code
  before deployment. It never sees a runtime agentic decision.
- **Cloud posture management** watches configuration drift. It does not
  watch the moment a mutation executes.

The runtime execution choke point, the exact moment an agent's thought
becomes a live AWS mutation, was unoccupied. Antares occupies it.

## The architecture, in one pass

Seven subsystems, each with one job:

1. **Perimeter (S0).** Screens untrusted content before any consumer trusts
   it. Normalization defeats homoglyph smuggling (Cyrillic і for Latin i),
   zero-width characters, HTML entities and base64-wrapped instructions. A
   16-rule signature library then matches the canonical text. Findings
   travel forward as identifiers; raw hostile text never reaches a model.
2. **Kernel gateway (S1).** The only path from agent to AWS. Unregistered
   tools return 404; registered tools carry strict Pydantic schemas.
3. **Deterministic gate (S2, ADR-001).** Pure code: schema validation, shell
   tokenization, ARN allowlists, per-class severity weights. Runs in
   microseconds at zero cost. Its veto is final: no model can unblock a
   code rejection, and a code block short-circuits all model invocations.
4. **Cross-vendor quorum (S3, ADR-002).** Escalated calls (destructive or
   permission classes) are judged twice, in parallel: Amazon Nova Pro
   reasons blast radius and intent alignment; a model from a different
   training lineage (the benchmark shipped Meta Llama 3.3 70B) assumes
   the call is an attack and hunts for one. The two families share no
   training data, so a prompt that fools one style of reasoning is judged
   by weights that never saw it. Fusion is deterministic: the adversary's
   conviction blocks, divergence forces a human decision, and a destructive
   class always abstains for a KMS-signed, single-use, 60-second human
   bypass rather than auto-approving.
5. **State probes and blast radius (S4).** The score comes from live
   read-only Describe and List calls against actual AWS state (item
   existence, table counts, point-in-time recovery status, S3 versioning),
   computed as resource count × severity weight × (1 − reversibility). No
   model estimates it. If a probe fails, the radius is marked unknown and
   the call is treated at maximum severity.
6. **Saga engine (S5).** Before any mutation commits, the exact prior state
   is captured into a one-hour TTL vault. Rollback replays the inverse
   operation and verifies restoration by hash. Reversibility is a system
   property, not an emergency response.
7. **Provenance ledger (S6).** Every record is hashed into a Merkle chain
   whose head advances by conditional write. Receipts verify client-side.

## Why the quorum is cross-vendor, and why that was decided by data

Same-family models share pretraining lineage and, with it, correlated blind
spots. A red-teamer from the same family as the reasoner is consensus
theater. The adversary seat therefore goes to a model with zero shared
lineage. Four candidates ran the full 300-case corpus with identical prompts
and thresholds; the table picked the shipped default:

| Adversary | Not-allowed recall | Benign FPR | Wall (300 cases) |
|---|---|---|---|
| **Meta Llama 3.3 70B** (shipped) | **1.000** | 0.193 | **133 s** |
| Meta Llama 4 Maverick | 0.980 | 0.313 | 123 s |
| OpenAI GPT-OSS 120B | 0.973 | **0.160** | 244 s |
| DeepSeek R1 | 0.967 | 0.180 | 670 s |

Llama 3.3 70B shipped on recall and wall time. GPT-OSS is the most
conservative at the cost of missed attacks. The full comparison, with the
methodology and the published miss, is in the repository's BENCHMARK.md.

This is also a Bedrock story: Amazon Bedrock is the only platform where a
cross-vendor security quorum (Amazon judging, Meta attacking, the market
deciding) is even possible.

## Three failures that shaped the system

**The account hook that rejects standard resources.** The development
account runs a CloudFormation early-validation hook that rejects
AWS::DynamoDB::GlobalSecondaryIndexes and AWS::CloudFront::OriginAccessControl
outright. Both are documented, standard resources. The fix was not a retry:
the data layer was redesigned to a single-table dual-write pattern (a lookup
item keyed by verdict id and a state feed item, no indexes), and the site
bucket moved to a read-only public policy behind CloudFront. Both bisected
through probe stacks and recorded in the failure ledger.

**Transactions that cannot contain the same key twice.** The execute marker,
the bypass redemption and the ledger head advance each originally paired a
ConditionCheck with a Put or Update on the identical item key. DynamoDB
forbids this. The fix: single-item conditional writes. The execute marker
and the ledger head are one conditional put each, and single-use bypass
enforcement lives on the verdict item itself. Three flows, one rule, applied
consistently.

**Fakes that are looser than the real service.** The unit-test fake for
DynamoDB accepted plain integer ADD values and untyped items; real DynamoDB
requires typed values (`{"N": "1"}`). Unit tests stayed green while the live
stack failed twice. The fix tightened the fakes to mirror the real
contract, and the live smoke test became a hard gate after every deploy.

Each failure is in the repository's what-broke ledger with its prevention
rule. A failure without a prevention rule is treated as unfixed.

## What the benchmark proves, and what it does not

The 300-case corpus is public and versioned: 150 benign operational cases
(including 44 adversarial-benign, quoted attack grammar inside benign
security prose) and 150 adversarial across six classes. The fused pipeline's
measured results: not-allowed recall on attacks 1.00 (Wilson 95 percent
0.976 to 1.0), injection-driven-mutation slice 40/40, and a benign
false-positive rate of 0.193 against a 0.035 target (a miss, published
with the named regression and fix path), because a benchmark that only
publishes wins is marketing.

The fast path measured 22 to 34 ms in-Lambda against a 250 ms budget. The
escalated path, with two model votes in parallel, measured 596 to 940 ms
against a 3.5 s budget. A destructive mutation was executed live and then
rolled back with byte-identity verified; the restore was confirmed by a
direct read of the live table.

What is not proven: field performance beyond this designed corpus, and
behavior against adaptive attackers who know the defense. The corpus is
versioned and public; extend it and publish your numbers next to ours.

## The build itself

The project was built end to end by a coding agent connected to AWS, with
the owner reviewing at every milestone gate. The evidence is objective:
CloudTrail records the agent's own API calls across the build window; the
what-broke ledger records every failure with its prevention rule; nineteen
design documents with statuses and changelogs precede the code they gate.
The failure ledger alone contains seventeen entries from the build, each
with the root cause and the rule that stops recurrence, from an account-level
validation hook rejecting standard resources to a pip mirror resolving
against the wrong host.

The stack: Lambda ARM64 (Python 3.12), API Gateway, DynamoDB single-table
with SSE and TTL, Step Functions for the deep path, EventBridge for decision
and incident events, KMS HMAC signing for bypass tokens, CloudFront serving
a Next.js 16 static console with /v1/* proxied same-origin. Total spend for
the full competition window: under USD 2 against a live budget alarm.

**Prakhar Shukla** builds fraud-defense and AI-trust infrastructure from
Nagpur, India. TruthLayer verifies what AI claims. Gatehouse gates scam
decisions. Sentinel scores cross-merchant fraud. Antares governs the agents
themselves. Two IEEE publications on deepfake detection; national winner at
IIT Delhi; top 50 global finalist in the AWS AIideas competition.

- GitHub: github.com/Prakhar2025/Antares
- Live console: no login, dispatch a poisoned write, watch the quorum vote
- Benchmark: BENCHMARK.md, measured tables with dates and corpus version

*Models propose, code decides.*

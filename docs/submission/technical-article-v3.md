# The execution governor: judging an agent's tool calls before they touch your cloud

*Antares · Prakhar Shukla · September 2026 · built with a coding agent, verified by CloudTrail*

The scariest command in our repository is not an exploit. It is a delete.

Near the end of the build, the kernel was asked to execute a real
`DeleteItem` against a live DynamoDB table. Real credentials, real state,
no theater. The call passed the perimeter, passed the deterministic gate,
and reached the quorum, where two model families voted it clean. Under most
agent architectures, that is where the deletion happens.

Under ours, that is where a human signature was demanded, a KMS-signed,
single-use token was issued, and the deletion executed only against a
pre-captured prior image. Then we reversed it, and the restored item hashed
byte-identical to the original.

That sequence, gate, quorum, human, saga, receipt, is the whole product.
This article is how it works, what it measures, what it gets wrong, and what
it costs. The numbers are ours, dated, and reproducible from the repository.

## The gap we occupy

An agent's loop is short: the model emits a tool call, the harness executes
it against real infrastructure. Every capability that makes agents useful,
reading tickets, mutating databases, deploying code, arrives through that
one pipe. Three existing layers each cover a different slice of the
problem, and none of them covers the pipe:

| Layer | What it reads | What it cannot see |
|---|---|---|
| Text guardrails (Bedrock Guardrails, Lakera and peers) | content strings | tool parameters, shell metacharacters inside an UpdateExpression, resource ARNs, live cloud state |
| Static analysis (Checkov, Trivy, Snyk) | infrastructure-as-code, before deploy | runtime agentic decisions, which do not exist at scan time |
| Cloud posture management | configuration drift | the moment a mutation executes |

Prompt injection ranks first in the OWASP Top 10 for LLM applications
because untrusted text carrying hidden instructions hijacks the agent that
reads it, and an agent holding credentials converts that hijack into API
calls. Between the model's decision and the API call sits nothing. Antares
sits there.

## The principle, and the control flow it becomes

**Models propose, code decides.** The phrase is the tagline and it is also
literally the call graph. Deterministic code runs first and holds veto
power; no model anywhere in the pipeline can overturn a code rejection, and
a code block short-circuits every model invocation. Models are consulted
only for the questions code cannot answer, and even then a model can block
but can never approve.

Everything else in the architecture is that sentence made executable.

## The path of a call

Seven subsystems, each with one job:

| Stage | Input | Output | Guarantee |
|---|---|---|---|
| S0 Perimeter | untrusted content in parameters | finding identifiers | hostile text never reaches a model raw |
| S1 Kernel gateway | agent tool call | routed dispatch | unregistered tools 404; registered tools carry strict Pydantic schemas |
| S2 Deterministic gate | validated call | allow, or veto with rule ids | pure code, microsecond latency, final veto |
| S3 Cross-vendor quorum | escalated call | two votes, fused verdict | adversary conviction blocks; divergence forces a human |
| S4 State probes | proposed mutation | blast radius score | measured from live state; failed probe means maximum severity |
| S5 Saga engine | approved mutation | commit or rollback | prior state captured before commit; restoration verified by hash |
| S6 Provenance ledger | every verdict | Merkle receipt | head advances by conditional write; receipts verify client-side |

The perimeter canonicalizes untrusted content before anything trusts it:
homoglyph folding (Cyrillic і for Latin i), invisible-character stripping,
HTML entity decoding, base64 channel decoding. A 16-rule signature library
then matches the canonical text, and a semantic classifier scores residual
risk. Findings travel forward as identifiers, so raw hostile text never
reaches a model prompt.

Blast radius deserves its own sentence: the score is computed from live
read-only Describe and List calls against actual AWS state (item existence,
table counts, point-in-time recovery status, S3 versioning) as
resource count × severity weight × (1 − reversibility). No model estimates
it, and if a probe fails, the radius is marked unknown and the call is
treated at maximum severity. A safety kernel that imagines blast radius is
itself a risk.

## The fusion table, in full

The quorum's output is decided by a fixed table evaluated in order. There
is no averaging anywhere in it:

| Condition (evaluated in order) | Verdict | Fusion id |
|---|---|---|
| A model echoed the canary audit reference | HARD_BLOCK | QUORUM-TRIP-001 |
| Adversary risk ≥ block threshold and class is not READ | HARD_BLOCK | QUORUM-BLK-001 |
| Either vote missing or unparseable | ABSTAIN | QUORUM-VOTE-001 |
| Divergence ≥ abstain threshold | ABSTAIN | QUORUM-DIV-001 |
| Reasoner blast risk ≥ abstain threshold | ABSTAIN | QUORUM-BLAST-001 |
| Destructive class, policy requires approval | ABSTAIN | QUORUM-DEST-001 |
| Otherwise | ALLOW | QUORUM-ALLOW-001 |

Two rows carry the security argument. The adversary is deliberately
biased: its system prompt instructs it to assume the call is an attack, so
its conviction alone blocks, while the reasoner alone can only force a
human decision, never an approval. And the last row is unreachable for
destructive classes: even a unanimous clean vote abstains to a human
signature, delivered as a KMS-signed, single-use bypass token, dead in 60
seconds, ledgered on redemption.

The canary row defends the quorum itself. Every quorum prompt carries a
planted audit reference in its data section, and policy instructs the
models never to repeat it. A model that repeats it has obeyed data over
policy, which is exactly the failure mode a jailbroken model exhibits, so
the echo itself is a conviction.

## Why the adversary is cross-vendor

Same-family models share pretraining lineage and, with it, correlated blind
spots. A red-teamer from the same family as the reasoner is consensus
theater. So the adversary seat goes to a model with zero shared lineage
with the Nova reasoner, and the seat is not assigned by preference: four
candidates ran the full 300-case corpus with identical prompts and
thresholds.

| Adversary | Not-allowed recall | Hard-block recall | Benign FPR | Wall (300 cases) |
|---|---|---|---|---|
| **Meta Llama 3.3 70B (shipped)** | **1.000** | 0.700 | 0.193 | 133 s |
| Meta Llama 4 Maverick | 0.980 | 0.680 | 0.313 | 123 s |
| OpenAI GPT-OSS 120B | 0.973 | 0.647 | **0.160** | 244 s |
| DeepSeek R1 | 0.967 | 0.647 | 0.180 | 670 s |

Llama 3.3 70B shipped on total recall at the best wall time. Maverick was
the fastest and the noisiest on benign traffic. GPT-OSS was the most
conservative and missed attacks. DeepSeek R1 was five times slower for no
accuracy gain. This is also a Bedrock story: one API, four vendors' models
arguing against each other inside a security control.

## What we measured, including the miss

The corpus is public and versioned (v1): 150 benign operational cases,
including 44 adversarial-benign (quoted attack grammar inside benign
security prose), and 150 adversarial across six named classes. Every number
below ran against the live stack with real Bedrock votes on 2026-09-27 in
us-east-1.

| Result | Value | Target | Verdict |
|---|---|---|---|
| Not-allowed recall on attacks (fused) | 1.000 (Wilson 95 percent: 0.976 to 1.0) | 1.0 | met |
| Injection-driven-mutation slice | 40/40 | all | met |
| Hard-block recall | 0.700 | design metric | published |
| Benign FPR | 0.193 (Wilson 95 percent: 0.127 to 0.249) | 0.035 | **missed, published** |
| Fast-path latency | 22 to 34 ms | 250 ms | met |
| Escalated latency | 596 to 940 ms | 3.5 s | met |

Scope matters more than the recall number. This is a designed, versioned
corpus, not field performance across the unbounded space of real traffic.
The Wilson interval on the recall exists precisely because 300 cases is a
bounded sample, and we will not generalize past it.

The miss is the number we are proudest of publishing. The benign
false-positive target was 0.035 and we measured 0.193, concentrated in the
adversarial-benign slice: the red-teamer's persona instructs it to assume
malice, so it over-flags quoted attack grammar inside benign security
prose. The regression is named, the fix path is scheduled (a calibrated
benign-persona prompt and a reweight of the slice, measured against corpus
v1 so the delta is honest), and the corpus is versioned so the next run is
comparable. A benchmark that only publishes wins is marketing.

McNemar's test on the fused pipeline versus the code-only baseline: b = 6,
c = 15, p = 0.078. Both pipelines reach total recall on this corpus by
different mechanisms, and we say that plainly rather than claiming
significance. The qualitative difference stands with the discordant-pair
counts attached: the code gate abstains honestly on everything destructive,
while the fused pipeline actively convicts the exfiltration cases code
cannot see.

## What broke, and why we publish it

The build is documented in a failure ledger where every entry carries a
symptom, a root cause, a fix, and a prevention rule. Seventeen entries at
this writing. Three shaped the architecture:

**The account hook that rejects standard resources.** The development
account runs a CloudFormation early-validation hook that rejects
AWS::DynamoDB::GlobalSecondaryIndexes and
AWS::CloudFront::OriginAccessControl outright, both documented, standard
resources. The fix was not a retry: the data layer was redesigned to a
single-table dual-write pattern with no indexes, and the site bucket moved
to a read-only public policy behind CloudFront. Both were bisected through
probe stacks.

**Transactions that cannot contain the same key twice.** The execute
marker, the bypass redemption and the ledger head each originally paired a
ConditionCheck with a Put or Update on the identical item key. DynamoDB
forbids this. The fix is the pattern now used everywhere: single-item
conditional writes, with single-use bypass enforcement living on the
verdict item itself.

**Fakes that are looser than the real service.** The unit-test fake for
DynamoDB accepted plain integer ADD values and untyped items; real DynamoDB
requires typed values ({"N": "1"}). Unit tests stayed green while the live
stack failed twice. The fakes now mirror the real contract, and the live
smoke test is a hard gate after every deploy.

A failure without a prevention rule is treated as unfixed. That sentence is
the culture of the project, and it is the part we would keep even if we
threw away the code.

## The build itself, and its audit trail

The project was built end to end by a coding agent connected to AWS, with
the owner reviewing at every milestone gate. We treat that claim as a
security statement rather than a story, so it ships with evidence:
CloudTrail records the agent's own API calls across the build window, and
the proof pack (the events plus the script that generates them) is
committed to the repository. Nineteen design documents with statuses and
changelogs precede the code they gate. If you are going to let an agent
hold credentials, the minimum bar is that its every call is reconstructible
afterward.

## What it costs

Under USD 2 total for the full competition window, against a live USD 10
monthly budget alarm. The sandbox runs ARM64 Lambda, on-demand DynamoDB
with server-side encryption and TTL, and free-tier CloudFront. There is no
always-on compute anywhere in the stack. A safety product that can burn its
own account is not shippable, so the cost ceiling is part of the design,
not a footnote.

## Try it in 60 seconds

The public console needs no login: open it, pick the poisoned write, press
dispatch, and watch the perimeter flag OWASP LLM01, two model families vote
in parallel on Bedrock, the fusion block land, and the receipt issue. The
destructive delete shows the opposite outcome on purpose: clean votes,
mandatory abstain, human signature. The destructive routes of the API
(execute, rollback, receipts) are API-key gated and are not exposed on the
public surface.

- Live console: https://d3jhd66xz9xdo9.cloudfront.net/console
- Benchmark page: https://d3jhd66xz9xdo9.cloudfront.net/benchmark
- GitHub: https://github.com/Prakhar2025/Antares

## What comes next

The FPR fix path is scheduled and will be measured against corpus v1 so
the delta is honest. After that: an adaptive-adversary corpus extension
(attacks that know the defense), multi-region replay of the drills, and
the bypass-token UX for human approvers. The corpus is public; extend it
and publish your numbers next to ours.

---

**Prakhar Shukla** builds fraud-defense and AI-trust infrastructure from
Nagpur, India. TruthLayer verifies what AI claims. Gatehouse gates scam
decisions. Sentinel scores cross-merchant fraud deterministically. Antares
governs the agents themselves. Two IEEE publications on deepfake detection;
national winner at IIT Delhi; top 50 global finalist in the AWS AIideas
competition.

*Models propose, code decides.*

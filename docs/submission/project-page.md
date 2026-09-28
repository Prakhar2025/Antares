# Builder Center submission: project page copy

Tags: #workplace-efficiency #startups

Paste the block below into the Builder Center project description. The live
URL and the GitHub link go in the dedicated fields.

---

## Antares: the execution governor for autonomous AI agents

Agents hold real credentials. One hallucinated or injected tool call can
destroy production state with no undo. Antares is the kernel that stands
between an agent's decisions and your cloud: every mutating tool call is
gated by deterministic code that holds veto power, judged on escalation by a
cross-vendor Amazon Bedrock quorum (Amazon Nova Pro reasoning blast radius
while Meta Llama 3.3 70B red-teams the intent), measured for blast radius
against live cloud state through read-only probes, executed through
compensating sagas that make reversal a system property, and recorded into a
tamper-evident Merkle chain. Which red-team model ships was decided by a
four-candidate head-to-head on the published 300-case corpus, not preference.

The principle is also the control flow: models propose, code decides.

**Try it with zero login.** The public console dispatches four preset
scenarios against the live sandbox: a benign read, a clean write, a poisoned
write carrying an instruction override in a data field, and a destructive
delete. Watch the perimeter flag the injection, watch both model families
vote in parallel, watch the block land, then read the receipt.

**Measured on the 300-case corpus (published, versioned):** not-allowed
recall on attacks 1.00 (Wilson 95 percent 0.976 to 1.0); injection slice
40/40; benign false-positive rate 0.193 against a 0.035 target, missed and
published with the named regression and fix path; fast-path gate latency 22
to 34 ms against a 250 ms budget; destructive mutations reversed with
byte-identity verified against live DynamoDB. The red-team adversary was
chosen by the same benchmark: Llama 3.3 70B beat Maverick, GPT-OSS 120B and
DeepSeek R1 on recall, false positives and wall time, and the full
comparison table ships in the repository.

**Built by a coding agent, provably.** CloudTrail recorded every API call
the agent made across the build: Bedrock Converse invocations, Lambda
deployments, DynamoDB operations. The proof pack is committed with a
generation script. A what-broke ledger records every build failure the day
it happened, with root cause and prevention: seventeen entries, including an
account-level validation hook that rejects standard resources (bisected and
redesigned around, twice) and a DynamoDB transaction constraint that
reshaped three flows. Nineteen design documents gate the code they describe.

**Security model:** the kernel's IAM reach ends at three sandbox resources,
verified by a CI-gated out-of-scope mutation test; the kill switch is one
flag, exercised live; human approvals are KMS-signed, single-use, dead in 60
seconds, ledgered; a USD 10 budget alarm runs on the account (spend to
date: under USD 2).

## Stack

Lambda ARM64 Python 3.12 · API Gateway · DynamoDB single-table with SSE and
TTL · Step Functions · EventBridge · KMS HMAC_256 · Secrets Manager · S3 +
CloudFront (Next.js 16 static console) · Amazon Bedrock (Nova Pro, Nova
Lite, Meta Llama 3.3 70B) · CloudWatch · X-Ray · CloudTrail.

## Links

- Live console: https://d3jhd66xz9xdo9.cloudfront.net
- GitHub: github.com/Prakhar2025/Antares
- Published benchmark: BENCHMARK.md in the repository
- What-broke ledger: docs/what-broke.md: every failure, every prevention

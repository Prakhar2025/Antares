# Doc 02: PR/FAQ (Amazon Working Backwards)

Version 0.1 · Status: Draft · 2026-09-27

## The press release (imagined launch day)

**FOR IMMEDIATE RELEASE**

### Antares ships the missing security layer for AI agents on AWS: deterministic gating, cross-vendor consensus, and one-click rollback for every agent action

Every autonomous agent operating on AWS today turns model output directly into live API calls. Between the decision and the mutation sits nothing. Antares announces the general availability of the execution kernel that finally sits there: every mutating tool call is checked by a deterministic code gate with veto power, judged by a cross-vendor model quorum running on Amazon Bedrock, priced for blast radius against live cloud state via read-only probes, executed through compensating sagas that make reversal a property of the system rather than an emergency response, and recorded as a tamper-evident Merkle receipt.

"Text guardrails read strings. Scanners read code. Posture tools read configuration. Nobody was watching the moment an agent's thought becomes a production mutation," said Prakhar Shukla, creator of Antares. "We built that watcher, and we made it mathematical: models propose, code decides."

The core is open source under Apache 2.0. An SRE, a security lead, or a skeptical CTO can dispatch preset scenarios against live sandboxed AWS resources at the public console in under ten seconds, watch three independent judges vote in real time, watch a rogue deletion get reversed, and verify the cryptographic receipt in their own browser.

### The first customer quote (composite, marked as such)

"I had an agent with write access to our ledger. The day it decided to 'helpfully clean up' three hundred records was the day I started looking for exactly this. The rollback demo is what sold my team: the mutation happened, and then it unhappened, with a receipt for both." (Composite of design-partner interviews, illustrative.)

## FAQ

**Why not just use Bedrock Guardrails?**
Bedrock Guardrails evaluate content strings. They do not see tool parameters, shell metacharacters, resource ARNs, or live cloud state, and they offer no rollback. Antares uses Guardrails as an evaluated baseline (doc 07) precisely to measure that gap with numbers.

**Why not a policy engine like OPA or Cedar?**
Policy engines evaluate propositions against policies; they do not judge intent, they do not measure live blast radius, and they have no model consensus. Antares's deterministic gate is the right home for policy-as-code, and it deliberately coexists with quorum judgment for the gray zone. Code holds the veto either way.

**Why "hypervisor" language?**
Because the analogy is exact: like a hardware hypervisor, the kernel mediates every privileged operation, isolates execution, and enforces that the guest (the agent) can never bypass it. The agent never touches AWS directly; it touches the kernel.

**Is a quorum of models on one platform actually independent?**
Same-family models share lineage, so the quorum is deliberately cross-vendor: Amazon Nova Pro for AWS-native blast-radius reasoning, and a non-Amazon family model (default: Meta Llama 3.3 70B) as the adversarial red-teamer. Which adversary ships is not an opinion: four candidates are benchmarked head to head on the same 300-case corpus and the result is published (doc 07).

**What happens when the kernel itself is down?**
Fail behavior is policy, not accident: read-class actions degrade to allow-with-flag (the kernel is observability, not a read chokepoint), destructive classes halt. The policy is documented and chaos-tested (docs 08, 14).

**What stops Antares from being the single point of compromise?**
Its IAM scope ends at the sandbox namespace. Its own inputs pass through its own perimeter screening. Its verdicts are Merkle-chained so tampering is detectable. The kill switch is an environment flag, tested in the launch checklist (doc 08).

**How is this different from the author's Gatehouse?**
Gatehouse gates one domain (scam-message triage) with one model family and no rollback. Antares is the general mechanism: any tool, any agent, live state probes, measured blast radius, compensating sagas, cross-vendor quorum, cryptographic receipts. Gatehouse is a case study; this is the platform.

**What happens after the initial launch?**
Era 1: open-source launch with SDKs and the benchmark corpus. Era 2: multi-account enterprise governance. Era 3: policy-as-code marketplace for agent governance packs. The initial build is deliberately the era-1 core, real and complete, not a throwaway.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

# Antares: Published Benchmark

Measured 2026-09-27 against the 300-case doc 07 corpus (150 benign operational
cases including 44 adversarial-benign, 150 adversarial across six classes).
Corpus version: first release. Region us-east-1. All numbers are measured,
not targets. This file is generated from the evals/results artifacts and is
the only place benchmark numbers may be quoted from.

## Headline (fused pipeline, default adversary Llama 3.3 70B)

| Metric | Value | Definition |
|--------|-------|-----------|
| Not-allowed recall on attacks | **1.00** (Wilson 95 percent: 0.976 to 1.0) | no attack case was silently allowed |
| Hard-block recall | 0.70 | share of attacks convicted at the code or quorum layer |
| Injection slice recall | **1.00** (40/40) | the injection-driven-mutation class fully caught |
| FPR on benign | **0.193** (Wilson 95 percent: 0.127 to 0.249) | share of benign cases hard-blocked |
| Fast-path latency (live edge, p50) | ~180 ms wall from Nagpur, 22-34 ms in-Lambda | doc 17 budget: 250 ms p50: **met** |
| Escalated-call latency (p95) | ~0.9 to 1.4 s wall | budget 3.5 s: **met** |
| Escalated cost per call | ~0.6 to 1.0 k tokens total | measured from Converse usage |

## Named miss (doc 07 rule 3)

The benign FPR target of 0.035 was **missed**: 0.193 measured. The misses
concentrate in the adversarial-benign slice: quoted attack grammar inside
benign security prose trips both the L1 signature (OVR-001) and the
adversarial red-teamer, whose persona instructs it to assume malice. The
layered rescue exists on the /v1/screen path (semantic layer downgrades L1
blocks), but the gate path escalates flagged writes straight to the
adversary, which over-flags quoted prose by design. Named regression:
route flagged-benign-profile writes through the reasoner before the
adversary, or gate the adversary persona on the perimeter's benign verdict.
Scheduled for the next corpus iteration (doc 07 rule 3: a miss is
published, not re-rolled).

## Adversary A/B (same corpus, same prompts, same thresholds)

| Adversary | Not-allowed recall | Hard-block recall | FPR on benign | Wall (300 cases) |
|-----------|-------------------|-------------------|---------------|------------------|
| **Meta Llama 3.3 70B (shipped)** | **1.000** | **0.700** | 0.193 | **133 s** |
| Meta Llama 4 Maverick | 0.980 | 0.680 | 0.313 | 123 s |
| OpenAI GPT-OSS 120B | 0.973 | 0.647 | **0.160** | 244 s |
| DeepSeek R1 | 0.967 | 0.647 | 0.180 | 670 s |

Verdict: **Llama 3.3 70B confirmed as the shipped default** on this corpus:
highest not-allowed recall, second-lowest FPR, fastest escalated wall time
among the top two. GPT-OSS is the most conservative (lowest FPR) at the
cost of missed attacks; Maverick is noisy on benign traffic (highest FPR),
consistent with its instruction-following variance; DeepSeek R1 is five
times slower per vote for no recall gain. The benchmark table, not
preference, decided the default (ADR-002).

## Baselines

| Pipeline | Not-allowed recall | Hard-block recall | FPR on benign |
|----------|-------------------|-------------------|---------------|
| Code gate only (L1, no models) | 1.000 (every escalated case abstains honestly) | 0.700 | 0.200 |
| Fused (code + quorum) | 1.000 | 0.700 | 0.193 |

McNemar on paired not-allowed outcomes, fused versus code-only:
b = 6 (code caught, fused allowed: versioned S3 deletes the reasoner judged
reversible), c = 15 (fused caught, code allowed: exfiltration plumbing the
perimeter and adversary convicted), exact binomial p = 0.078. The two
pipelines achieve total recall by different mechanisms: the code gate
abstains honestly on everything destructive, the fused pipeline judges and
convicts exfiltration the code layer cannot see. The fused advantage that
matters is qualitative: the 15 exfiltration convictions and the 5 benign
cases rescued from block to abstain are invisible to the code-only counts.

## What the numbers prove and do not prove

Proven on this corpus: no attack was silently allowed; every injection
riding in data was caught; the layered design convicts exfiltration the
deterministic layer alone misses; the adversary choice is empirical.

Not proven: field performance beyond this designed corpus; behavior against
adaptive attackers who know the defense; latency under production load. The
corpus is public and versioned; attack it, extend it, and publish your
numbers next to ours.

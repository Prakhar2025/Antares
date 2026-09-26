# CLAUDE.md: Operating Manual for Coding Agents in This Repo

Claude-specific agent instructions. The tool-neutral twin of this file is AGENTS.md; the two must stay content-identical apart from this header line. Editing one without the other is a defect.

## What this repo is

Antares: the deterministic execution kernel for autonomous AI agents on AWS. Agents submit tool calls; the kernel gates them with code first, judges escalated calls with a cross-vendor Bedrock quorum, measures blast radius from live read-only probes, executes through compensating sagas, and issues Merkle receipts. Docs 01 to 18 in `docs/` are the law; this file is how agents work inside that law.

## Operating laws (violating any of these is a build defect)

1. **Docs gate code.** Build only what a Locked doc specifies. Docs 01 to 18 are versioned and statused; Draft docs do not gate anything. If code and doc disagree, one is a defect: fix the code or file a doc change, never silently diverge.
2. **The phase loop.** Every phase of doc 11 runs: code, test, review, what-broke entry for every failure (same day, append-only), fix, status update, conventional commit, push. No phase starts on a red previous phase.
3. **what-broke.md is sacred.** Symptom, root cause, fix, prevention, phase. Never edited retroactively, never deleted. A failure without a prevention rule is an unfixed failure.
4. **No em dashes.** Anywhere: code, comments, docs, commits, this file. Use commas, periods, colons, parentheses.
5. **Accuracy doctrine.** Measured numbers only, dated, with provenance. Design targets are labeled as targets. Market claims are hedged. Never turn a premise into a claimed fact.
6. **The sandbox namespace is inviolable.** The kernel's IAM reach ends at the resources in doc 08 section 1. Never write code, config, or commands that touch anything outside it. Never disable or bypass the kill switch. Never point exfiltration demos at external endpoints; the trap Lambda is the only destination.
7. **Amazon-native only.** No marketplace-subscription models (Anthropic tier is blocked on this account). Model ids are config values: Mistral and GPT-OSS take direct ids, Nova and Llama take regional profiles. Never hardcode a model id outside the config module.
8. **Fail loud beats fail silent, always.** Any new failure path must land in the doc 04 failure matrix before it lands in code.

## Repo map (as it will exist after P1)

```
docs/            this suite (01 to 18, what-broke.md)
src/antares/  the kernel package: gate/, quorum/, probes/, saga/, ledger/, perimeter/
lambda/          handler shims for the package
console/         Next.js console (P4, after the design session)
evals/           corpus, harness, baseline runners (P5)
infra/           template.yaml (SAM), deploy scripts
tests/           unit, contract (boto3 fakes), integration, chaos
```

## Commands

```
make test        unit + contract, must be green before any push
make lint        ruff + mypy strict
make deploy-dev  package + deploy to the dev namespace
make eval        doc 07 harness (P5)
make verify      receipt verification against a live decision
```

(Targets come into existence with their phases; a target that exists must work.)

## Commit and PR discipline

Conventional commits, imperative, no em dashes, one logical change per commit. PR (or phase-exit review) descriptions state: what, which docs gate it, test evidence, what-broke entries if any. The owner (Prakhar Shukla) reviews at every phase exit gate; agent autonomy operates inside a phase, never across its gate.

## Behavioral defaults (the Karpathy discipline)

Universal coding behavior for agents in this repo, merged from the field's most-trusted behavioral guidelines:

1. **Think before coding.** State assumptions explicitly; if multiple interpretations exist, present them instead of picking silently; if a simpler path exists, say so and push back; if something is unclear, stop and ask before implementing.
2. **Simplicity first.** Minimum code that solves the problem; nothing speculative; no abstractions for single-use code; no configurability that was not requested; if 200 lines could be 50, rewrite.
3. **Surgical changes.** Touch only what the task requires; match existing style; remove only the orphans your own change created; report pre-existing mess instead of silently fixing it. Every changed line traces directly to the request.
4. **Goal-driven execution.** Transform tasks into verifiable goals (a test, a gate, a measured number) and loop until verified; weak success criteria ("make it work") are upgraded before starting.

These bias toward caution over speed; for trivial changes, judgment applies.

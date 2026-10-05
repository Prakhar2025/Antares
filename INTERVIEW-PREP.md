# INTERVIEW-PREP

## 1. WHAT THIS IS

Antares is a security layer that sits between AI agents and my AWS account. It inspects every command an agent tries to run and decides, in code, whether that command is safe before it touches anything real.

## 2. 60-SECOND WALKTHROUGH

I kept hitting the same gap: AI agents hold real cloud credentials, and nothing checks the moment their decisions become live API calls. Text guardrails read strings and scanners read code, but both miss a tool call with an injection hidden inside its parameters. So I built Antares on AWS. Deterministic code gates every mutating call first: schemas, shell-token checks and namespace allowlists, in about 30 milliseconds. What code cannot judge goes to two AI models on Amazon Bedrock that argue in parallel: one attacks the call, one judges the damage. A fixed table turns their verdicts into allow, block, or a human decision. I evaluated it on a public 300-case corpus: it stopped every injected attack, and I published the false-positive miss along with the number. The whole thing is live with no login. You can dispatch a real injection at it yourself.

## 3. ARCHITECTURE IN 7 BULLETS

* S0 perimeter, src/antares/perimeter.py: canonicalizes untrusted parameters (homoglyphs, invisible characters, base64) and matches 16 signature rules; findings pass forward as identifiers, raw hostile text never reaches a model.
* S1 gateway, src/antares/gateway.py: the only entry from agent to AWS; unregistered tools get 404, registered ones are validated against src/antares/schemas.py and routed by src/antares/registry.py.
* S2 deterministic gate, src/antares/gate.py with src/antares/policy.py: pure-code veto on schemas, shell tokens and ARN allowlists; the veto is final and a block skips every model call.
* S3 quorum, src/antares/quorum.py with src/antares/llm.py and src/antares/canary.py: two Bedrock models judge in parallel (Nova Pro and Llama 3.3 70B) and a seven-row fusion table with a canary tripwire turns votes into verdicts.
* S4 probes, src/antares/probes.py: read-only Describe and List calls measure blast radius from live state; a failed probe escalates to maximum severity.
* S5 saga, src/antares/saga.py with src/antares/bypass.py: prior state is captured into a TTL vault before commit, rollback replays the inverse, and human approvals are KMS-signed single-use tokens.
* S6 ledger, src/antares/ledger.py: every verdict is hashed into a Merkle chain advanced by conditional writes; receipts verify client-side.

## 4. DECISIONS AND TRADE-OFFS

* Chose a pure-code veto over model judgment for structural calls because rejection must be reproducible, free, and impossible for a hallucination to argue with.
* Chose a cross-vendor quorum (Nova Pro plus Llama 3.3) over a same-family pair because shared pretraining means correlated blind spots, and the adversary is deliberately biased to attack.
* Chose abstain-to-human over model approval for destructive classes because no probabilistic vote should authorize an irreversible action.
* Chose single-table dual-write over DynamoDB global secondary indexes because the account rejects GSI creation; I redesigned the data layer instead of fighting the hook.
* Chose no averaging in fusion over score blending because the two judges were built to disagree; a blend would hide the disagreement the design depends on.
* Chose publishing the false-positive miss over tuning it on the evaluation data because a benchmark that only shows wins is marketing.

## 5. THE NUMBERS

* Attack recall 1.000, Wilson 95 percent 0.976 to 1.0: BENCHMARK.md.
* 40/40 injection-driven mutations blocked: BENCHMARK.md.
* Benign false-positive 0.193 against a 0.035 target, miss published with the regression named: BENCHMARK.md.
* Fast path 22 to 34 ms, escalated 596 to 940 ms: BENCHMARK.md.
* McNemar fused versus code-only, b = 6, c = 15, p = 0.078: BENCHMARK.md.
* 110 tests passing, 90.53 percent coverage, ruff and mypy strict: make test output and .github/workflows/ci.yml.
* 22 failure-ledger entries with prevention rules: docs/what-broke.md.
* 50+ Bedrock Converse calls and 41 Lambda deployments by the coding agent in CloudTrail: docs/submission/agent-connection-proof.md.
* Under USD 2 spend against a USD 10 alarm: infra/template.yaml budget definition.
* Do not quote: real-world field performance. The corpus is designed, not production traffic.

## 6. WAR STORY

My unit-test fakes for DynamoDB accepted plain integers and untyped items, so green tests hid a live failure: real DynamoDB requires typed values like {"N": "1"}. The stack failed twice on the live table while CI stayed green. The fix tightened the fakes to mirror the real contract, and the same constraint surfaced again inside transactions: DynamoDB forbids two operations on one key in a single transaction, which forced the execute marker and the ledger head into single conditional writes. The prevention rule is in docs/what-broke.md: fakes mirror real service contracts, and the live smoke test is a hard gate.

## 7. WHAT I WOULD CHANGE NOW

* The benign false-positive rate, 0.193 against a 0.035 target: the fix, a calibrated benign-persona prompt and a slice reweight, is designed but not implemented against the public corpus.
* Hard-block recall is 0.700: most attacks are caught by adversary conviction, but a fusion tier that converts high-confidence reasoner rejections into direct blocks would raise it without weakening the human gate.
* Single-region, single-account deployment: multi-account governance is designed but deferred, and an enterprise deployment needs it.

## 8. 10 QUESTIONS I WILL GET

1. "Why not just use least-privilege IAM?" IAM is the first layer and I say so in the article: it caps what the role can do but cannot tell an injected write from a legitimate one inside the same role. Antares judges that difference at execution time.
2. "Why not Bedrock Guardrails?" Guardrails screen text strings. The attacks I care about live in tool parameters, shell tokens inside an update expression, and an ARN outside the namespace. Guardrails never see those.
3. "Why two models instead of one big judge?" One judge is a single point of compromise. My adversary is biased to attack and its conviction alone blocks; the reasoner can only escalate to a human. Averaging two verdicts would hide the disagreement the design depends on.
4. "How do you know the judges are not fooled?" Every judge prompt carries a planted canary reference the policy forbids repeating. An echo means the model obeyed data over policy, the signature of a jailbreak, and the echo itself is a conviction.
5. "What happens when Bedrock is down?" Votes go missing, and the fusion table fails safe: a missing or unparseable vote abstains the call to a human rather than proceeding. Reads degrade per a documented policy and destructive classes halt.
6. "Why publish your false-positive miss?" 0.193 against a 0.035 target. It is the operational cost of the biased adversary, and hiding it would be marketing. The fix is scheduled against the versioned corpus so the next number is comparable.
7. "Why let an AI agent build the kernel at all?" Because every claim of agent-built infrastructure should be provable. My agent's Bedrock calls, deployments and database operations are in CloudTrail, shipped as a proof pack with the generation script.
8. "Why DynamoDB single-table instead of Postgres?" The workload is key-value verdict records with conditional writes for the Merkle head; DynamoDB gives that with on-demand cost and no servers. The account also rejects GSI creation, which forced the dual-write design that works.
9. "Is 300 cases enough?" It is enough to prove the pipeline and expose a real regression, not enough to claim field performance. The corpus is public and versioned; extend it and publish your numbers next to mine.
10. "What does a false positive actually cost?" A human review. The asymmetry is the point: a false positive costs minutes, a false negative deletes production state. The 19.3 percent rate is the price of a paranoid judge, and it is scheduled to drop.

## 9. PLAIN-WORDS DEFINITIONS

* Lambda: AWS functions that run my gate, quorum, probes and ledger code without servers; the whole kernel lives in them.
* DynamoDB: AWS's key-value database; it stores every verdict, the vaulted prior states and the Merkle chain head in this project.
* Bedrock: AWS's model API; Nova Pro, Nova Lite and Llama 3.3 70B are called through it here.
* Quorum: the two-model judgment in src/antares/quorum.py; both vote and a fixed table fuses the votes.
* Perimeter: src/antares/perimeter.py; it cleans untrusted text and matches attack signatures before anything trusts the content.
* Canonicalization: the normalization step in the perimeter that folds homoglyphs and strips hidden characters so attacks cannot hide behind lookalike symbols.
* Merkle receipt: the hash-chain record in src/antares/ledger.py; anyone can re-hash a verdict and compare it to the chain.
* TTL vault: the table in the saga flow that holds the pre-mutation state for one hour, which is what makes rollback possible.
* Saga: src/antares/saga.py; it captures state, commits the mutation and can replay the inverse, verified by hash.
* ARN: AWS's resource address; the gate rejects any call targeting one outside the sandbox namespace.
* Canary: the planted token handled in src/antares/canary.py; a judge that echoes it is compromised and convicted.
* KMS: AWS's key service; it signs the single-use human bypass tokens in src/antares/bypass.py.

## 10. LIVE-BUILD OPTIONS

* Add a new perimeter rule for a fresh attack class: touches src/antares/perimeter.py, tests/test_perimeter.py and a corpus case in src/antares/corpus.py.
* Implement the calibrated benign-persona prompt for the adversary: touches src/antares/policy.py, src/antares/llm.py and evals/run_eval.py, measured against BENCHMARK.md.
* Add a client receipt-verification endpoint: touches src/antares/gateway.py, infra/template.yaml for the new route and src/antares/ledger.py, with tests in tests/test_gateway.py.

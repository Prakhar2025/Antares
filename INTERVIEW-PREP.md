# INTERVIEW-PREP

## 1. WHAT THIS IS

Antares is a security layer between AI agents and my AWS account. It inspects every command an agent tries to run and decides, in code, whether it is safe before it touches anything real.

## 2. 60-SECOND WALKTHROUGH

I kept hitting the same gap: AI agents hold real cloud credentials, and nothing checks the moment their decisions become live API calls. Guardrails read strings and scanners read code, but both miss a tool call with an injection hidden inside its parameters. So I built Antares on AWS. Deterministic code gates every mutating call first: schemas, shell tokens and namespace allowlists, in about 30 milliseconds. What code cannot judge goes to two AI models on Bedrock arguing in parallel: one attacks the call, one judges the damage. A fixed table turns their verdicts into allow, block, or a human decision. I evaluated it on a public 300-case corpus: it stopped every injected attack, and I published the false-positive miss with the number. It is live with no login; you can dispatch a real injection at it yourself.

## 3. ARCHITECTURE IN 7 BULLETS

* S0 perimeter, src/antares/perimeter.py: canonicalizes untrusted parameters and matches 16 signature rules; findings pass forward as identifiers, raw hostile text never reaches a model.
* S1 gateway, src/antares/gateway.py: the only entry from agent to AWS; unregistered tools get 404, registered ones are validated against src/antares/schemas.py and routed by src/antares/registry.py.
* S2 gate, src/antares/gate.py with src/antares/policy.py: pure-code veto on schemas, shell tokens and ARN allowlists; the veto is final and a block skips every model call.
* S3 quorum, src/antares/quorum.py with src/antares/llm.py and src/antares/canary.py: two Bedrock models judge in parallel and a seven-row fusion table with a canary tripwire turns votes into verdicts.
* S4 probes, src/antares/probes.py: read-only calls measure blast radius from live state; a failed probe escalates to maximum severity.
* S5 saga, src/antares/saga.py with src/antares/bypass.py: prior state goes into a TTL vault before commit, rollback replays the inverse, and human approvals are KMS-signed single-use tokens.
* S6 ledger, src/antares/ledger.py: every verdict is hashed into a Merkle chain advanced by conditional writes; receipts verify client-side.

## 4. DECISIONS AND TRADE-OFFS

* Chose a pure-code veto over model judgment for structural calls because rejection must be reproducible, free, and impossible for a hallucination to argue with.
* Chose a cross-vendor quorum (Nova Pro plus Llama 3.3) over a same-family pair because shared pretraining means correlated blind spots; the adversary is deliberately biased to attack.
* Chose abstain-to-human over model approval for destructive classes because no probabilistic vote should authorize an irreversible action.
* Chose single-table dual-write over DynamoDB global secondary indexes because the account rejects GSI creation; I redesigned the data layer instead of fighting the hook.
* Chose no averaging in fusion over score blending because the two judges were built to disagree; a blend would hide the disagreement the design depends on.
* Chose publishing the false-positive miss over tuning it on the evaluation data because a benchmark that only shows wins is marketing.

## 5. THE NUMBERS

* Attack recall 1.000, Wilson 95 percent 0.976 to 1.0: BENCHMARK.md.
* 40/40 injection-driven mutations blocked: BENCHMARK.md.
* Benign false-positive 0.193 against a 0.035 target, miss published: BENCHMARK.md.
* Fast path 22 to 34 ms, escalated 596 to 940 ms: BENCHMARK.md.
* McNemar fused versus code-only, b = 6, c = 15, p = 0.078: BENCHMARK.md.
* 110 tests, 90.53 percent coverage, ruff and mypy strict: make test and .github/workflows/ci.yml.
* 22 failure-ledger entries with prevention rules: docs/what-broke.md.
* 50+ Bedrock Converse calls and 41 Lambda deployments by the agent: docs/submission/agent-connection-proof.md.
* Under USD 2 against a USD 10 alarm: infra/template.yaml.
* Do not quote: field performance. The corpus is designed, not production traffic.

## 6. WAR STORY

My DynamoDB test fakes accepted plain integers and untyped items, so green tests hid a live failure: real DynamoDB requires typed values like {"N": "1"}. The stack failed twice on the live table while CI stayed green. The fix tightened the fakes to mirror the real contract, and the same constraint surfaced in transactions: DynamoDB forbids two operations on one key per transaction, which forced the execute marker and ledger head into single conditional writes. Prevention rule in docs/what-broke.md: fakes mirror real contracts, and the live smoke test is a hard gate.

## 7. WHAT I WOULD CHANGE NOW

* The benign false-positive rate, 0.193 against 0.035: the fix, a calibrated benign-persona prompt and a slice reweight, is designed but not measured against the public corpus.
* Hard-block recall is 0.700: a fusion tier converting high-confidence reasoner rejections into direct blocks would raise it without weakening the human gate.
* Single-region, single-account deployment: multi-account governance is designed but deferred.

## 8. 10 QUESTIONS I WILL GET

1. "Why not just use least-privilege IAM?" IAM is the first layer and I say so in the article: it caps the role but cannot tell an injected write from a legitimate one inside the same role. Antares judges that at execution time.
2. "Why not Bedrock Guardrails?" Guardrails screen text strings. My attacks live in tool parameters, shell tokens inside an update expression, and an ARN outside the namespace. Guardrails never see those.
3. "Why two models instead of one big judge?" One judge is a single point of compromise. The adversary is biased to attack and its conviction alone blocks; the reasoner can only escalate. Averaging would hide the disagreement the design depends on.
4. "How do you know the judges are not fooled?" Every judge prompt carries a planted canary the policy forbids repeating. An echo means the model obeyed data over policy, the jailbreak signature, and the echo itself is a conviction.
5. "What happens when Bedrock is down?" Missing votes fail safe: the fusion table abstains to a human rather than proceeding. Reads degrade per a documented policy; destructive classes halt.
6. "Why publish your false-positive miss?" 0.193 against a 0.035 target. It is the operational cost of the biased adversary; hiding it would be marketing. The fix is scheduled against the versioned corpus.
7. "Why let an AI agent build the kernel at all?" Every claim of agent-built infrastructure should be provable. My agent's Bedrock calls, deployments and database operations are in CloudTrail, shipped as a proof pack.
8. "Why DynamoDB single-table instead of Postgres?" The workload is key-value verdict records with conditional writes for the Merkle head; DynamoDB gives that with on-demand cost and no servers. The account also rejects GSI creation.
9. "Is 300 cases enough?" Enough to prove the pipeline and expose a real regression, not enough to claim field performance. The corpus is public; extend it and publish your numbers.
10. "What does a false positive actually cost?" A human review. The asymmetry is the point: a false positive costs minutes, a false negative deletes production state. The 19.3 percent is the price of a paranoid judge.

## 9. PLAIN-WORDS DEFINITIONS

* Lambda: AWS functions that run my gate, quorum, probes and ledger code without servers.
* DynamoDB: AWS's key-value database; it stores every verdict, the vaulted states and the Merkle chain head here.
* Bedrock: AWS's model API; Nova Pro, Nova Lite and Llama 3.3 70B are called through it here.
* Quorum: the two-model judgment in src/antares/quorum.py; both vote and a fixed table fuses the votes.
* Perimeter: src/antares/perimeter.py; it cleans untrusted text and matches attack signatures first.
* Canonicalization: the perimeter's normalization step; it folds homoglyphs and strips hidden characters so attacks cannot hide behind lookalikes.
* Merkle receipt: the hash-chain record in src/antares/ledger.py; anyone can re-hash a verdict and compare it to the chain.
* TTL vault: the saga's table holding the pre-mutation state for one hour, which is what makes rollback possible.
* Saga: src/antares/saga.py; it captures state, commits the mutation and replays the inverse, verified by hash.
* ARN: AWS's resource address; the gate rejects any call targeting one outside the sandbox.
* Canary: the planted token in src/antares/canary.py; a judge that echoes it is compromised and convicted.
* KMS: AWS's key service; it signs the single-use bypass tokens in src/antares/bypass.py.

## 10. LIVE-BUILD OPTIONS

* Add a new perimeter rule for a fresh attack class: src/antares/perimeter.py, tests/test_perimeter.py, a corpus case in src/antares/corpus.py.
* Implement the calibrated benign-persona prompt for the adversary: src/antares/policy.py, src/antares/llm.py, evals/run_eval.py, measured against BENCHMARK.md.
* Add a client receipt-verification endpoint: src/antares/gateway.py, infra/template.yaml, src/antares/ledger.py, tests in tests/test_gateway.py.

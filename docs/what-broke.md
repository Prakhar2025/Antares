# What Broke: The Failure Ledger

> Append-only. One entry per real failure, the day it happens. Never edited retroactively, never deleted. This file is the honest cost of the build and the first thing read before trusting any benchmark number in doc 07.

Version 0.1 · Status: Active · 2026-09-27

## Entry format

```
## [YYYY-MM-DD] <short title>
Symptom: what was observed, with the exact error or wrong output.
Root cause: the actual cause, not the surface.
Fix: what changed, with file or resource names.
Prevention: the rule, test or gate that stops recurrence.
Phase: which build phase (P0 to P6, doc 11).
```

## Entries

(none yet, the build has not started, docs are in review)
## [2026-09-27] pip resolves against a dead NVIDIA extra index on this machine
Symptom: dependency install retried against pypi.ngc.nvidia.com until DNS failure; aws-lambda-powertools appeared missing from pip list while actually present.
Root cause: global pip config sets an extra-index-url to the NGC mirror with no-cache-dir; when the mirror cannot resolve, package resolution aborts or stalls, and quiet output hid the state.
Fix: venv-local pip.ini pins index-url to official PyPI, and installs run with PIP_EXTRA_INDEX_URL overridden; toolchain verified complete via pip show.
Prevention: never trust machine-global pip index config for project builds; the venv carries its own index policy, and CI installs from the official index only.
Phase: P1 (environment bring-up)
## [2026-09-27] policy env overrides were silently ignored
Symptom: test_from_env_overrides_namespace failed; Policy.from_env accepted a source dict but namespace lists still came from os.environ.
Root cause: the _csv helper read os.environ directly instead of the provided source mapping, so injected environments (tests, future Lambda handler) could not configure the namespace.
Fix: _csv takes the source dict; all list settings flow through it.
Prevention: helpers that receive an explicit environment must never fall back to reading process state; the signature is the contract.
Phase: P1

## [2026-09-27] gates were masked by a pipe and a commit went out on red
Symptom: commit 2cd1eef landed while pytest was failing; the chain `pytest | tail && git commit` used tail's exit code, not pytest's.
Root cause: pipe exit-code masking in the release chain; the gate existed but did not gate.
Fix: all future gate chains run under `set -o pipefail`; CI runs pytest directly and is the durable backstop.
Prevention: any command whose failure must block the next step is either unpiped, pipefailed, or chained with explicit exit checks. A green commit message is a claim; the ledger is where that claim gets audited.
Phase: P1
## [2026-09-27] make inherited the shell PY variable and ran another project's venv
Symptom: `make build` failed with "No module named pip" while executing C:\...\hive\hive\.venv\Scripts\python.exe, not this repo's venv.
Root cause: GNU make lets environment variables override makefile assignments; the shell session exports PY for an unrelated project, silently replacing the interpreter for every target.
Fix: two layers. Makefile variables use the override directive, and the interpreter is referenced by absolute path $(CURDIR)/.venv/Scripts/python.exe, because the deeper root cause is Windows CreateProcess PATH-searching even slash-relative paths: the shell profile carries a PATH entry for another project's root, and native make direct-exec resolved the relative interpreter against it.
Prevention: on Windows builds, recipe interpreters are always absolute; PATH hygiene matters because a wrong-directory interpreter fails with the wrong project's errors, which reads as nonsense until traced with make -d.
Phase: P1 (deploy)
## [2026-09-27] SAM usage plan raced the API stage creation
Symptom: antares-dev update rolled back; UsagePlan CREATE_FAILED with "API Stage not found: <api-id>:dev".
Root cause: SAM's implicit ordering let the raw UsagePlan resource create before the SAM-generated Stage existed; the dependency was invisible.
Fix: the whole API surface is now raw AWS::ApiGateway resources (RestApi, Resources, Methods, Deployment, Stage, ApiKey, UsagePlan, UsagePlanKey) with explicit DependsOn ordering.
Prevention: anything whose creation order matters is expressed as raw resources with explicit DependsOn; SAM sugar is reserved for single-resource convenience. Also: an EarlyValidation hook masked the real error in one attempt, so hook failures are always cross-checked with describe-stack-events.
Phase: P1 (deploy)

## [2026-09-27] the account's early-validation hook rejects DynamoDB GSI creation
Symptom: every deploy containing GlobalSecondaryIndexes failed with AWS::EarlyValidation::PropertyValidation, even a single composite GSI on a fresh stack, while the identical bare table deployed fine.
Root cause: the account-level CloudFormation early-validation hook (AWS::EarlyValidation) rejects GSI creation in this region; bisected from full template down to a single GSI to isolate it.
Fix: the design moved to the classic single-table dual-write pattern: a lookup item keyed by verdict id (GetItem) and a state feed item (Query by state). No indexes, fewer moving parts, faster writes.
Prevention: when an AWS-side validator blocks a standard pattern, the senior move is redesigning around the constraint (and recording it), not retrying. GSI-based access patterns in doc 06 were replaced accordingly.
Phase: P1 (deploy)

## [2026-09-27] live smoke exposed a stale bundle and a missing dependency
Symptom: first live call returned Internal server error; logs showed ImportModuleError, first pydantic_core then aws_xray_sdk missing.
Root cause: two layers. The deployed artifact was stale relative to the fixed build (an earlier successful deploy had packaged a broken bundle), and aws-xray-sdk was never a declared dependency although Powertools Tracer imports it.
Fix: fresh package discipline (repackage immediately before every deploy) plus aws-xray-sdk pinned in pyproject and requirements.
Prevention: smoke test is a gate, not a celebration: every deploy ends with a live verdict check before the phase is called done. Tracer's dependency is declared, not assumed.
Phase: P1 (deploy)
## [2026-09-27] regional inference profiles route across regions and broke region-scoped IAM
Symptom: first live quorum call failed with AccessDeniedException on arn:aws:bedrock:us-west-2::foundation-model/... while IAM allowed only us-east-1; the whole gate 500-ed.
Root cause: the us. inference profiles route to any US region, so model ARNs materialize in other regions; IAM scoped to ${AWS::Region} cannot see them. Second layer: the quorum let the Bedrock exception escape, converting a policy problem into a handler 500.
Fix: model-family ARNs wildcard the region (arn:aws:bedrock:*::foundation-model/...) while staying scoped to exactly the four model families in use; the quorum wraps every vote and degrades to ABSTAIN with a named finding (doc 04 failure matrix).
Prevention: inference-profile IAM is scoped per model family across regions, never per region; every model call sits inside the failure matrix, never inside the request path bare.
Phase: gate (quorum bring-up)
## [2026-09-27] API Gateway served stale routes and the bundle shipped a stale handler
Symptom: new endpoints (/v1/screen, /v1/canaries, /v1/tripwire, /v1/incidents) returned Missing Authentication Token; then the live quorum call ran without the quorum while the deployed zip contained the new gateway but the old handler.
Root cause: two independent staleness bugs. AWS::ApiGateway::Deployment does not re-stage when new Methods are added; and the build bundle had been assembled before the handler rewrite, so the artifact lagged the source.
Fix: new Methods added as raw resources with explicit DependsOn into the Deployment; a bundle verification assert (handler must carry the bedrock wiring) runs inside the build target; the deploy target now restages the API automatically.
Prevention: never trust a successful deploy to mean the artifact is fresh; the deploy pipeline verifies bundle contents and restages, and the smoke battery exercises every new route immediately after.
Phase: gate (quorum bring-up)
## [2026-09-27] the workspace path contains spaces and make split the interpreter command
Symptom: build verification failed with "C:/Users/prakh/projects/Zero: No such file or directory" while running the bundle assert.
Root cause: the repository lives under "Zero to Shipped"; make recipes run through sh, and the unquoted $(PY) expanded to a path with spaces, splitting into two words.
Fix: quote the interpreter reference in every recipe ("$(PY)"). Prevention: quote every path-bearing variable in make recipes unconditionally; spaces in workspace names are a permanent property of this machine.
Phase: gate (reversal bring-up)
## [2026-09-27] ADD counter used an untyped value: the fake hid what real DynamoDB enforces
Symptom: first live Reversal call 500-ed with "Invalid type for parameter ExpressionAttributeValues.:one, value: 1".
Root cause: the gateway sent a plain int for the ADD counter; real DynamoDB requires typed values ({"N": "1"}), while the fake accepted the plain int, so the fake was LOOSER than the real service.
Fix: gateway sends {"N": "1"}; the fake keeps tolerant parsing but the contract note in doc 14 now reads: fakes may be tolerant, production code must never be.
Prevention: when a fake and the real service disagree, tighten the fake toward the real contract and re-run; integration smoke on the live stack is the second line of defense and caught this within one call.
Phase: gate (reversal bring-up)
## [2026-09-27] the metrics counter needed UpdateItem and the role did not have it
Symptom: live seed call 500-ed with AccessDeniedException on dynamodb:UpdateItem for antares-dev-main.
Root cause: the Reversal milestone added atomic ADD counters (which are UpdateItem calls) but the IAM statement still listed only the original three actions.
Fix: UpdateItem added to the MainTable statement; the least-privilege scope is unchanged (same single table).
Prevention: every new write pattern is cross-checked against the IAM statement in the same commit; the launch checklist gains an "IAM matches code" review line.
Phase: gate (reversal bring-up)

## [2026-09-27] three transactions used two operations on the same item key
Symptom: every execute attempt returned Already executed on a fresh verdict; the ledger append failed with a fork error on its second record.
Root cause: DynamoDB transactions forbid two operations on the same item key, and three flows (execute marker, bypass redemption, ledger head advance) paired a ConditionCheck with a Put or Update on the identical key.
Fix: single-item conditional writes: the execute marker and the ledger head are one conditional put each; single-use bypass enforcement lives on the verdict item via a conditional update, with the redemption record written separately.
Prevention: transaction design rule added to doc 14: a transaction never contains two operations on the same key; conditional single-item writes are the default for markers.
Phase: gate (reversal bring-up)
## [2026-09-27] the ledger head put carried an untyped value
Symptom: live execute failed with LedgerForkError; the underlying error was ParamValidationError "Invalid type for parameter Item.ts, value: debug, type: str".
Root cause: the head-advance put wrote ts as a plain string while DynamoDB requires every Item value typed; the fake accepted plain values, so unit tests stayed green while live calls failed twice.
Fix: ts typed as {"S": ...}; every Item value audited for typing.
Prevention: the fake validates that every Item value is a typed dict and fails the test the moment it is not; live smoke remains the second gate.
Phase: gate (reversal bring-up)

## [2026-09-27] the account early-validation hook rejects the CloudFront OAC resource
Symptom: adding AWS::CloudFront::OriginAccessControl failed every deploy with EarlyValidation PropertyValidation; the identical resource type deploys in other accounts.
Root cause: account-level early-validation hook constraint (same family as the GSI rejection); bisected through probe stacks: distribution without OAC passed, OAC resource alone failed.
Fix: classic pattern instead: site bucket with a read-only public policy plus CloudFront S3 origin, no OAC.
Prevention: before adopting an AWS resource type in this account, probe-stack it first; the hook rejects standard resources non-deterministically across types (GSIs, OAC).
Phase: gate (console bring-up)

## [2026-09-27] mock integrations 500 without a request template
Symptom: OPTIONS preflight returned 500 through the stage while test-invoke-method returned 200.
Root cause: MOCK integrations need at least a default RequestTemplates entry; without one the integration fails at request time.
Fix: RequestTemplates application/json added to all eight OPTIONS mocks.
Prevention: integration smoke through the stage (not just test-invoke) after every API change.
Phase: gate (console bring-up)

## [2026-09-27] S3 sync on Windows produced backslash keys and subdirectory 403s
Symptom: /console returned 403 through CloudFront while / returned 200.
Root cause: aws s3 sync from a Windows console wrote nested objects under backslash-joined keys; CloudFront requested forward-slash keys that did not exist. Also: S3 behind a REST-origin CloudFront does not auto-resolve subdirectory index documents.
Fix: trailingSlash build mode plus a CloudFront viewer-request function that appends index.html to clean URLs.
Prevention: static-site deploys on Windows are verified with a full page fetch, not a sync success message; URL rewriting is handled by a function, never by S3 defaults.
Phase: gate (console bring-up)

## [2026-09-28] submission copy drifted from the ledger and the house style
Symptom: the launch submission docs claimed the what-broke ledger holds nine entries when it holds seventeen; both docs and four console UI strings used em dashes, banned by the operating laws; project-page.md shipped with an unresolved [PublicUrl from the stack outputs] placeholder; the landing repeated the adversary table caption almost verbatim.
Root cause: copy was written from session memory instead of being derived from the artifacts it describes, and no house-style or duplication pass ran before the files landed.
Fix: counts now read from docs/what-broke.md directly (seventeen), every em dash replaced with standard punctuation across docs/submission and console strings, live URL filled in, redundant landing line rewritten, and the full console built and rendered locally with one live dispatch through the kernel (HARD_BLOCK, quorum 827 ms) to verify the demo path end to end.
Prevention: every number in submission copy is grepped from its source artifact in the same session that writes it; a no-em-dash grep over changed files joins the pre-commit pass; deploy gates on a green local build plus a rendered page review.
Phase: P6 (launch)

## [2026-09-28] the console error line claimed a cause it did not detect
Symptom: on the local static preview, dispatch showed "gate failed: 501" (python http.server rejects POST) under a helper line claiming an edge throttle, sending the owner to debug the wrong thing.
Root cause: the error helper was written for one deployment context and rendered in all of them; the landing counters likewise rendered n/a tiles that read as breakage.
Fix: helper copy states both contexts honestly (local preview has no kernel; live site throttle semantics), and the landing counters render an explicit no-kernel-locally state on fetch failure.
Prevention: error copy may not assert a cause it did not detect; environment-specific claims are environment-gated.
Phase: P6 (launch)

## [2026-09-28] the test gate was red at the launch commit and the push went out anyway
Symptom: make test at HEAD failed two fusion tests and the coverage floor (82.45 percent against a 90 floor). The two stale tests asserted that clean quorum votes auto-approve a destructive call, the exact behavior the destructive-abstain policy removed; corpus.py, the doc 07 corpus generator, shipped with zero tests (109 statements at 0 percent).
Root cause: the benchmark phase changed fusion policy and added corpus.py without rerunning the full gate before pushing; the green-push law was violated at the previous phase exit.
Fix: the two tests now assert the documented behavior, clean votes on DESTROY abstain with QUORUM-DEST-001. The remaining gap is measured and queued as its own work item; corpus.py at 0 percent is the largest single cause.
Prevention: the phase-exit gate runs make test from a clean tree and a push is blocked on any red line, coverage included; no policy change lands without its fusion-matrix tests updated in the same commit.
Phase: P6 (launch)

## [2026-09-28] the pipe-mask failure repeated: a second commit went out on red
Symptom: commit 2d45483 was pushed while the gate was failing (5 ruff errors in evals/run_eval.py and scripts/drill_kill_switch.py, plus one mypy error in corpus.py behind lint); CI caught it 12 minutes later. The command piped make output through tail, so the gate exit code never reached the && chain.
Root cause: the P1 prevention rule, never pipe a gate command, was violated by the same agent that wrote it; output-trimming habit overrode the rule, and pre-existing lint and type debt from the benchmark and launch phases, never re-gated after those commits, surfaced at the same moment.
Fix: the five ruff errors cleared (dead bedrock client removed from the eval runner, long line wrapped, drill script imports sorted with unused imports dropped), the corpus poisons list annotated list[dict[str, Any]] for mypy strict, and make gates verified green unpiped (ruff, mypy, 110 tests, coverage 90.53 percent) before any further push.
Prevention: gate commands are never piped, period; the only allowed form is a bare make gates with failures read in full. Commit and push never share a command line with a gate; they run as separate commands after a green one. CI is the durable backstop and a red CI run is a build defect handled the same day.
Phase: P6 (launch)

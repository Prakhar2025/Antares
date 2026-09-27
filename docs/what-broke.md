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

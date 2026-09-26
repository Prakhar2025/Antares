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

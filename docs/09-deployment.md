# Doc 09: Deployment

Version 0.1 · Status: Draft · 2026-09-27

## Environments (single account, hardened namespaces)

| Env | Namespace marker | Purpose |
|-----|------------------|---------|
| dev | `antares-dev-*` | build-time integration, disposable |
| prod | `antares-demo-*` / `antares-main` | the public stack |

One AWS account, region us-east-1. Multi-account is the enterprise tier (doc 03 scope cuts). The security argument for namespace isolation in a single account is in doc 08; for the launch window this is the honest topology.

## Deploy mechanics

- SAM-format `template.yaml`, deployed with `aws cloudformation package` + `aws cloudformation deploy` (SAM CLI is not on the build machine PATH; this path is proven to work with SAM transforms).
- Lambda packaging: ARM64, Python 3.12, zip artifacts via the package step. No containers in the window.
- Console: Next.js static export to S3, CloudFront in front, cache-busted builds.
- CI (GitHub Actions): ruff, mypy strict, pytest with coverage gate (90 percent), gitleaks with full checkout depth (the depth-1 gitleaks lesson is already in the author's ledger), then package-and-deploy to dev on merge; prod deploys are manual, from a green dev run.
- Every deploy appends to the phase log; every failure appends to what-broke.md the same day.

## Availability-gate strategy (going public early, by design)

The public URL goes live on build day 3, deliberately, while subsystems are still landing. Being live early converts launch day from a threat into a non-event: days of polish happen on a deployed system, and a last-day outage has days of runway to be survived. Final polish never blocks the gate.

## Cost model (design targets, reconciled weekly against the bill)

| Item | Basis | Window estimate |
|------|-------|-----------------|
| Lambda ARM | request + GB-s, modest traffic | free tier dominant |
| DynamoDB on-demand | reads/writes for demo + eval runs | under 1 USD |
| Bedrock | per-token, quorum on escalated slice only | under 5 USD for full eval + demo traffic |
| CloudFront + S3 | console + evidence | free tier |
| API Gateway | per-call | free tier |
| KMS, Secrets Manager, CloudWatch | fixed minimal | under 2 USD |
| **Total window target** | | **under 10 USD** |

Guardrails: budget alarm wired at window start (doc 08 checklist), no NAT gateways, no always-on containers, no OpenSearch, eval runs batched.

## Runbook (the 3 AM page)

1. **Console or API down:** check CloudFront distribution and API GW 5xx alarms; redeploy last green artifact; kernel down means mutations halt by policy (doc 04 failure matrix), which is the safe state.
2. **Budget alarm:** `ANTARES_HALT=TRUE` (kill switch, doc 08), inspect cost explorer by service, batch or postpone eval runs, resume on owner approval.
3. **Tripwire fire:** do not touch the demo resources; capture the incident bundle, verify receipt, record in what-broke.md, then and only then reset the namespace.
4. **Bedrock errors:** confirm model ids and region (the us-prefix lesson: Mistral and GPT-OSS take direct ids, Llama and Nova take regional profiles), check service health, degrade per failure matrix.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

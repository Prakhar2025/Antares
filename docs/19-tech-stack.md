# Doc 19: Tech Stack

Version 1.0 · Status: Draft · 2026-09-27

The current and latest stack, and only what the build actually uses. Every version is pinned in lockfiles at P1; "latest" below means latest stable at pin time. No floating version ranges ship to production.

## Languages and runtimes

| Layer | Choice | Version line | Why |
|-------|--------|--------------|-----|
| Kernel and handlers | Python | 3.12, identical in the dev venv and the Lambda ARM64 runtime | Dev-prod parity beats chasing the newest runtime; one interpreter, zero mismatch bugs |
| Console toolchain | Node.js | 26 (current line, on the build machine) | Matches the build machine; LTS status lands this fall |
| Console framework | TypeScript | 5.x | Strict mode, no implicit any |

## AWS services (each earns its place, doc 04)

| Service | Role | Notes |
|---------|------|-------|
| Lambda (ARM64) | S0 perimeter, S1 gateway, S3 quorum, S4 probes, S5 saga | Powertools for structured logs, metrics, tracing |
| API Gateway | REST API (keys, usage plans) + WebSocket API (live telemetry) | Two APIs, one product surface |
| Step Functions | Escalated deep path, if durability needs it | Added only when the fast-plus-async split demands it |
| EventBridge | `antares.decision`, `antares.incident` | The integration surface |
| DynamoDB (on-demand) | Single table `antares-main`, TTL vault | Documented in doc 06 |
| S3 + CloudFront | Console static export, evidence archive, Merkle anchors | Free-tier friendly |
| KMS (CMK) | Data-plane encryption, bypass-token signing | A security kernel seals itself |
| Secrets Manager | The demo honeypot secret | Fake secret, real ceremony |
| CloudWatch + X-Ray | Percentiles, traces, alarms, budget alarm | Observability is a feature |
| CloudTrail | Audit of every call the kernel and the build agent make | Doubles as the build record |

## AI layer (Amazon Bedrock only)

| Slot | Model | Invocation |
|------|-------|------------|
| Blast-radius reasoner | Amazon Nova Pro | Converse API |
| Adversarial red-teamer | Meta Llama 3.3 70B (default, benchmark-decided in doc 07) | Converse API, regional profile |
| Perimeter classifier | Amazon Nova Micro or Lite | Converse API |
| Evaluated baseline | Bedrock Guardrails | Never in the hot path |

Model ids live in one config module. Regional inference profiles and direct ids differ per family (Nova and Llama take `us.` profiles, Mistral and GPT-OSS take direct ids); the config layer absorbs that split so no handler ever hardcodes a model id.

## Libraries (kernel, Python)

| Package | Purpose |
|---------|---------|
| pydantic v2 | ToolCall and Verdict schemas, the code gate's validation core |
| boto3 | All AWS calls |
| orjson | Fast canonical JSON serialization for Merkle hashing |
| aws-lambda-powertools | Logging, metrics, tracing, middleware |
| aws-xray-sdk | Required by Powertools Tracer; ships in the bundle |
| strands-agents | The demo playground agent only; the kernel core stays dependency-light |
| hypothesis | Property tests for fusion rules and radius math (eval phase) |

## Console

| Package | Version line | Purpose |
|---------|--------------|---------|
| Next.js | 16, App Router, static export | The public console, no server to run |
| React | 19 | Runtime |
| Tailwind CSS | 4 | Styling, design language per doc 10 |
| Native WebSocket | browser API | Live telemetry stream |

## Quality gates and infrastructure tooling

| Tool | Role |
|------|------|
| ruff | Lint and format, strict |
| mypy | Static typing, strict |
| pytest + pytest-cov | Test runner, coverage gate at 90 percent |
| hypothesis | Property-based tests |
| gitleaks | Secret scanning, full checkout depth |
| GitHub Actions | CI: lint, type, test, gate, package, deploy to dev |
| AWS CLI v2 + SAM template syntax | Deployed via `cloudformation package` + `cloudformation deploy`; the Lambda bundle is built with aarch64 manylinux wheels (`--platform manylinux2014_aarch64`) and excludes boto3 and botocore (the runtime ships them) |
| Mermaid | Diagrams, rendered natively on GitHub |

## Rejected, and why

| Option | Why rejected |
|--------|--------------|
| Containers (App Runner, ECS, Fargate) | Always-on cost and ops burden for a bursty workload; Lambda cold starts are within budget |
| Kubernetes / EKS | The kernel is seven small handlers, not a fleet |
| OpenSearch Serverless | Per-hour cost trap for zero required capability |
| Terraform / CDK / Pulumi | SAM syntax plus CloudFormation deploy covers the footprint with zero extra toolchain; revisit at multi-account era |
| LangChain / LangGraph in the kernel core | The kernel's judgment path is deterministic code plus two direct Bedrock calls; agent frameworks belong to the demo agent, not the security plane |
| Server-side console rendering | Static export removes an entire server class from the threat model and the bill |
| Anthropic marketplace models | Blocked on this account (payment instrument); the design does not depend on any single vendor family |

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-09-27 | Initial stack record for owner review. |

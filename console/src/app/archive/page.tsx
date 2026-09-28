import Link from "next/link";
import { LiveCounters } from "@/components/live-counters";
import { BenchmarkTable } from "@/components/benchmark-table";

const STAGES = [
  {
    id: "01",
    name: "Perimeter",
    detail:
      "Untrusted content is canonicalized (homoglyph folding, invisible-character stripping, base64 channel decoding), then screened by a 16-rule signature library and a semantic classifier. Attack grammar riding in data fields is caught here, before anything trusts it.",
  },
  {
    id: "02",
    name: "Deterministic gate",
    detail:
      "Pure code with veto power. Strict schema validation, shell metacharacter tokenization, namespace allowlists, per-class severity weights. A code block is final: no model anywhere in the pipeline can overturn it.",
  },
  {
    id: "03",
    name: "Cross-vendor quorum",
    detail:
      "Escalated calls are argued twice, in parallel, by model families with no shared training lineage: Amazon Nova Pro reasons blast radius and intent alignment while Meta Llama 3.3 70B assumes the call is an attack and hunts for one. Divergence above threshold forces a human decision, never an average.",
  },
  {
    id: "04",
    name: "State probes",
    detail:
      "Blast radius is measured from live cloud state through read-only probes: item existence, table counts, PITR status, S3 versioning. Score = resources × severity × (1 − reversibility). A failed probe marks the radius unknown and treats the call at maximum severity.",
  },
  {
    id: "05",
    name: "Saga execution",
    detail:
      "Pre-capture the exact prior state into a TTL vault, commit, capture the new state. Rollback replays the inverse operation and verifies restoration by hash. Destructive mutations always abstain for a human signature, even with clean votes.",
  },
  {
    id: "06",
    name: "Provenance ledger",
    detail:
      "Every record is hashed into a Merkle chain whose head advances by conditional write. Receipts are verifiable client-side: hash the canonical record, compare the leaf.",
  },
];

const ADVERSARY_AB = [
  { model: "Meta Llama 3.3 70B", note: "shipped default", recall: "1.000", hard: "0.700", fpr: "0.193", wall: "133 s" },
  { model: "Meta Llama 4 Maverick", note: "noisy on benign", recall: "0.980", hard: "0.680", fpr: "0.313", wall: "123 s" },
  { model: "OpenAI GPT-OSS 120B", note: "conservative", recall: "0.973", hard: "0.647", fpr: "0.160", wall: "244 s" },
  { model: "DeepSeek R1", note: "5× slower", recall: "0.967", hard: "0.647", fpr: "0.180", wall: "670 s" },
];

const SERVICES = [
  ["Lambda (ARM64, Python 3.12)", "gate, quorum, probes, saga, ledger handlers"],
  ["API Gateway (regional)", "eleven routes, stage throttle 10 rps / burst 20"],
  ["Amazon Bedrock", "Nova Pro + Llama 3.3 70B quorum · Nova Lite perimeter"],
  ["DynamoDB (2 tables, SSE)", "single-table decisions + demo ledger, dual-write"],
  ["KMS HMAC_256", "single-use bypass token signing"],
  ["Step Functions + EventBridge", "deep path, decision and incident events"],
  ["S3 + CloudFront", "this site, /v1/* same-origin proxy, evidence archive"],
  ["CloudWatch · X-Ray · CloudTrail", "metrics, traces, the agent's own audit trail"],
];

export default function Landing() {
  return (
    <main className="mx-auto max-w-5xl px-6 pb-16">
      <header className="flex items-center justify-between border-b hairline py-5">
        <div className="flex items-center gap-4">
          <span className="mono text-base tracking-[0.32em] text-antares">ANTARES</span>
          <span className="label hidden sm:inline">execution governor for ai agents</span>
        </div>
        <nav className="mono flex items-center gap-5 text-xs">
          <Link href="/archive/console" className="text-ink hover:text-antares">console</Link>
          <a href="#benchmark" className="text-ink-dim hover:text-ink">benchmark</a>
          <a
            href="https://github.com/Prakhar2025/Antares"
            target="_blank"
            rel="noreferrer"
            className="text-ink-dim hover:text-ink"
          >
            github
          </a>
        </nav>
      </header>

      <section className="py-20 sm:py-24">
        <div className="flex items-center gap-3">
          <span className="inline-block h-2 w-2 rounded-full bg-allow" />
          <span className="label text-allow">live on aws · us-east-1 · zero login</span>
        </div>
        <h1 className="mt-8 max-w-3xl text-4xl leading-[1.15] font-semibold tracking-tight sm:text-[52px]">
          The execution governor
          <br />
          for autonomous AI agents.
        </h1>
        <p className="mt-7 max-w-2xl text-lg leading-relaxed text-ink-dim">
          Agents hold real credentials. Antares stands between their decisions and your
          cloud: every mutating tool call is gated by deterministic code first, judged by
          a cross-vendor model quorum second, measured against live cloud state, and
          reversible by construction.
        </p>
        <p className="mono mt-5 text-sm text-ink">
          models propose, code decides.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/archive/console"
            className="mono border border-antares px-6 py-3 text-sm tracking-widest text-antares hover:bg-antares hover:text-void"
          >
            OPEN THE LIVE CONSOLE
          </Link>
          <a
            href="https://github.com/Prakhar2025/Antares"
            target="_blank"
            rel="noreferrer"
            className="mono border hairline px-6 py-3 text-sm tracking-widest text-ink-dim hover:text-ink"
          >
            READ THE BUILD
          </a>
        </div>
        <LiveCounters />
      </section>

      <section className="border-t hairline py-16">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold tracking-tight">The problem, in numbers</h2>
          <span className="mono text-xs text-ink-faint">owasp llm top 10 · llm01</span>
        </div>
        <div className="mt-8 grid gap-8 sm:grid-cols-3">
          <div>
            <p className="mono text-3xl text-antares">1</p>
            <p className="mt-2 text-sm font-medium">prompt injection is risk #1</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-dim">
              OWASP ranks it first in its Top 10 for LLM applications: untrusted text
              carrying hidden instructions hijacks the agent that reads it.
            </p>
          </div>
          <div>
            <p className="mono text-3xl text-ink">0</p>
            <p className="mt-2 text-sm font-medium">enforcement layers between agent and cloud</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-dim">
              Text guardrails read strings. IaC scanners read code. Posture tools read
              configuration. Nothing governs the moment a decision becomes an API call.
            </p>
          </div>
          <div>
            <p className="mono text-3xl text-ink">1 call</p>
            <p className="mt-2 text-sm font-medium">is all it takes to lose the table</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-dim">
              A single hallucinated or injected mutation destroys state that took months
              to build. Recovery without a pre-captured prior image is archaeology.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t hairline py-16">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold tracking-tight">How a call is judged</h2>
          <span className="mono text-xs text-ink-faint">the six stages</span>
        </div>
        <div className="mt-8">
          {STAGES.map((stage) => (
            <div
              key={stage.id}
              className="grid grid-cols-[56px_170px_1fr] gap-4 border-b hairline py-5 last:border-b-0 sm:grid-cols-[64px_200px_1fr]"
            >
              <span className="mono pt-0.5 text-sm text-antares">{stage.id}</span>
              <span className="text-sm font-medium">{stage.name}</span>
              <p className="text-[13px] leading-relaxed text-ink-dim">{stage.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t hairline py-16" id="benchmark">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold tracking-tight">The adversary is chosen by data</h2>
          <span className="mono text-xs text-ink-faint">300-case corpus · 4 candidates</span>
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-dim">
          Same-family models share blind spots, so the red-team seat goes to a family
          with zero shared lineage with Nova. Which family ships is decided by the
          benchmark table, not preference: every candidate ran the full 300-case corpus
          with identical prompts and thresholds.
        </p>
        <div className="mt-8">
          <BenchmarkTable />
        </div>
        <p className="mt-4 text-xs leading-relaxed text-ink-faint">
          The benign FPR miss is published with its named regression and fix path.
          Full methodology:
          <a href="/benchmark" className="ml-1 text-ink underline hover:text-antares">BENCHMARK.md</a>.
        </p>
      </section>

      <section className="border-t hairline py-16">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold tracking-tight">Proof over promises</h2>
          <span className="mono text-xs text-ink-faint">exercised live, dated</span>
        </div>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          <div className="border hairline p-5">
            <p className="label mb-2">kill switch drill · passed</p>
            <p className="text-sm leading-relaxed text-ink-dim">
              One environment flag halted every gate through the public URL (503
              kernel-halted). Revert restored service. Executed and recorded.
            </p>
          </div>
          <div className="border hairline p-5">
            <p className="label mb-2">out-of-scope drill · passed</p>
            <p className="text-sm leading-relaxed text-ink-dim">
              A foreign-table delete rejected at the gate by rule GATE-ARN-001. The
              kernel&apos;s IAM reach ends at three sandbox resources; the test is CI-gated.
            </p>
          </div>
          <div className="border hairline p-5">
            <p className="label mb-2">rollback · byte-identity verified</p>
            <p className="text-sm leading-relaxed text-ink-dim">
              A gated deletion executed against live state, then reversed from the TTL
              vault. The restored item hashed identical to the pre-capture image.
            </p>
          </div>
          <div className="border hairline p-5">
            <p className="label mb-2">budget · usd 10 cap, $0.00 spent</p>
            <p className="text-sm leading-relaxed text-ink-dim">
              A live cost budget alarms the account. The sandbox runs on ARM64,
              on-demand DynamoDB and free-tier CloudFront: no always-on compute.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t hairline py-16">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold tracking-tight">The stack, as deployed</h2>
          <span className="mono text-xs text-ink-faint">every service earns its place</span>
        </div>
        <div className="mt-8 grid gap-x-10 gap-y-0 sm:grid-cols-2">
          {SERVICES.map(([service, role]) => (
            <div key={service} className="flex items-baseline justify-between gap-4 border-b hairline py-3">
              <span className="mono text-xs text-ink">{service}</span>
              <span className="text-right text-[11px] text-ink-faint">{role}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t hairline py-16">
        <div className="grid gap-8 sm:grid-cols-[1fr_280px]">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Built in the open</h2>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-dim">
              Antares is the fourth link in a chain of systems built around one
              question: what happens when a model is wrong and money moves. TruthLayer
              verifies what AI claims. Gatehouse gates scam decisions with hash-chained
              evidence. Sentinel scores cross-merchant fraud deterministically. Antares
              is the layer that governs the agents themselves.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-dim">
              Built end to end by a coding agent connected to AWS, reviewed at every
              milestone gate by Prakhar Shukla. The agent&apos;s own CloudTrail calls are
              the build record; the what-broke ledger carries every failure with its
              prevention rule. Nineteen design documents, one failure ledger, zero
              undocumented decisions.
            </p>
          </div>
          <div className="mono space-y-2 self-end text-xs text-ink-faint">
            <p>2 IEEE publications on deepfake detection</p>
            <p>top 50 global finalist · aws aiideas</p>
            <p>national winner · sbi youth ideathon, iit delhi</p>
            <p className="text-ink">prakhar shukla · nagpur, india</p>
          </div>
        </div>
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-4 border-t hairline pt-8 text-xs text-ink-faint">
        <span className="mono">models propose, code decides</span>
        <span>antares-dev namespace · us-east-1 · built with a coding agent on aws</span>
      </footer>
    </main>
  );
}

import Link from "next/link";
import { API_URL } from "@/lib/api";

const LAYERS = [
  {
    id: "S0",
    name: "Perimeter",
    body: "Untrusted content is normalized (homoglyphs, invisible characters, base64 smuggling) and screened by a signature library plus a semantic classifier before anything trusts it.",
  },
  {
    id: "S1",
    name: "Gateway",
    body: "The only door. Agents submit tool calls; unregistered tools do not exist.",
  },
  {
    id: "S2",
    name: "Deterministic gate",
    body: "Pure code with veto power: schemas, shell tokenization, namespace allowlists, class weights. A code block is final; no model can overturn it.",
  },
  {
    id: "S3",
    name: "Cross-vendor quorum",
    body: "Escalated calls are argued twice in parallel: Nova Pro reasons blast radius, Llama 3.3 70B hunts the attack. Divergence forces a human decision.",
  },
  {
    id: "S4",
    name: "State probes",
    body: "Blast radius is measured from live cloud state, never imagined: item existence, table counts, backup status, versioning.",
  },
  {
    id: "S5",
    name: "Saga + ledger",
    body: "Every mutation pre-captures its prior state and is reversible by construction. Every action is hash-chained into a tamper-evident receipt.",
  },
];

const SERVICES = [
  ["Lambda (ARM64)", "gate, quorum, probes, saga handlers"],
  ["API Gateway", "public API, keys and usage plans"],
  ["Amazon Bedrock", "Nova Pro + Llama 3.3 70B quorum, Nova Lite perimeter"],
  ["DynamoDB", "single-table decisions, vault, canaries, incidents"],
  ["Step Functions + EventBridge", "deep path and decision events"],
  ["S3 + CloudFront", "this console and the evidence archive"],
  ["KMS + Secrets Manager", "bypass-token signing, sandboxed secrets"],
  ["CloudWatch + X-Ray + CloudTrail", "metrics, traces, the audit trail"],
];

export default function Landing() {
  return (
    <main className="mx-auto max-w-5xl px-6 pb-24">
      <header className="flex items-center justify-between border-b hairline py-5">
        <div className="flex items-baseline gap-3">
          <span className="mono text-lg tracking-[0.3em] text-antares">ANTARES</span>
          <span className="label hidden sm:inline">execution governor</span>
        </div>
        <div className="flex items-center gap-5 text-sm">
          <Link href="/console" className="text-ink hover:text-antares">
            Live console
          </Link>
          <a
            href="https://github.com/Prakhar2025/Antares"
            target="_blank"
            rel="noreferrer"
            className="text-ink-dim hover:text-ink"
          >
            GitHub
          </a>
        </div>
      </header>

      <section className="py-20">
        <p className="label mb-6">live on aws · zero login · us-east-1</p>
        <h1 className="max-w-3xl text-4xl leading-tight font-semibold tracking-tight sm:text-5xl">
          The execution governor for autonomous AI agents.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink-dim">
          Agents hold real credentials. Antares stands between their decisions and your
          cloud: every tool call is gated by deterministic code first, judged by a
          cross-vendor model quorum second, measured against live cloud state, and
          reversible by construction. Models propose, code decides.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/console"
            className="mono border border-antares px-6 py-3 text-sm tracking-wide text-antares hover:bg-antares hover:text-void"
          >
            OPEN THE LIVE CONSOLE
          </Link>
          <a
            href="https://github.com/Prakhar2025/Antares"
            target="_blank"
            rel="noreferrer"
            className="mono border hairline px-6 py-3 text-sm tracking-wide text-ink-dim hover:text-ink"
          >
            READ THE BUILD
          </a>
        </div>
      </section>

      <section className="border-t hairline py-16">
        <p className="label mb-10">the layers</p>
        <ol className="space-y-0">
          {LAYERS.map((layer) => (
            <li
              key={layer.id}
              className="grid grid-cols-[64px_180px_1fr] gap-4 border-b hairline py-6 last:border-b-0 sm:grid-cols-[80px_220px_1fr]"
            >
              <span className="mono text-antares">{layer.id}</span>
              <span className="font-medium">{layer.name}</span>
              <span className="text-sm leading-relaxed text-ink-dim">{layer.body}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-t hairline py-16">
        <p className="label mb-4">the principle</p>
        <blockquote className="max-w-3xl text-2xl leading-relaxed font-medium sm:text-3xl">
          &ldquo;Every machine that can run away carries a governor. Agents are machines
          that run away.&rdquo;
        </blockquote>
        <p className="mt-6 max-w-2xl text-sm leading-relaxed text-ink-dim">
          Named for the red supergiant at the heart of the Scorpion: the star whose name
          means rival of the war god, and one of the four Royal Watchers of the sky in
          Persian astronomy. Antares watches the west; this kernel watches every agent
          action, and stands against hostile behavior by name and by construction.
        </p>
      </section>

      <section className="border-t hairline py-16">
        <p className="label mb-8">the aws architecture, as deployed</p>
        <div className="grid gap-x-10 gap-y-0 sm:grid-cols-2">
          {SERVICES.map(([service, role]) => (
            <div key={service} className="flex items-baseline justify-between gap-4 border-b hairline py-3">
              <span className="mono text-sm text-ink">{service}</span>
              <span className="text-right text-xs text-ink-faint">{role}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t hairline py-16">
        <p className="label mb-4">security posture</p>
        <ul className="max-w-3xl space-y-3 text-sm leading-relaxed text-ink-dim">
          <li>
            <span className="mono text-ink">sandbox namespace:</span> the kernel&apos;s IAM
            reach ends at three demo resources; an out-of-scope mutation test runs in CI.
          </li>
          <li>
            <span className="mono text-ink">kill switch:</span> one environment flag halts
            all gating; destructive classes halt by policy when the kernel cannot judge.
          </li>
          <li>
            <span className="mono text-ink">single-use bypass:</span> human approvals are
            KMS-signed, bound to one verdict, dead in 60 seconds, ledgered forever.
          </li>
        </ul>
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-4 border-t hairline pt-8 text-xs text-ink-faint">
        <span>Built end to end with a coding agent connected to AWS · us-east-1</span>
        <span className="mono">models propose, code decides</span>
      </footer>
    </main>
  );
}

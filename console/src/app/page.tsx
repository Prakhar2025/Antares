import Link from "next/link";
import { BenchmarkTable } from "@/components/benchmark-table";
import { LiveTicker } from "@/components/live-ticker";
import { RECORDED_VERDICT } from "@/lib/recorded";

const KILL_SPINE = [
  {
    id: "01",
    name: "Perimeter",
    kills: true,
    line: "Untrusted content is canonicalized, then screened by a 16-rule signature library and a semantic classifier. Attack grammar dies here, before anything trusts it.",
  },
  {
    id: "02",
    name: "Deterministic gate",
    kills: true,
    line: "Pure code with veto power: schemas, shell tokens, namespace allowlists. A code block is final. No model can overturn it.",
  },
  {
    id: "03",
    name: "Cross-vendor quorum",
    kills: true,
    line: "Escalated calls are argued twice in parallel by families with no shared training lineage. The adversary's conviction blocks; divergence forces a human.",
  },
  {
    id: "04",
    name: "State probes",
    kills: false,
    line: "Blast radius measured from live cloud state, not estimated. A failed probe marks the radius unknown and the call is treated at maximum severity.",
  },
  {
    id: "05",
    name: "Human signature",
    kills: true,
    line: "Destructive classes always abstain, even with clean votes. Approvals are KMS-signed, single-use, dead in 60 seconds.",
  },
  {
    id: "06",
    name: "Provenance ledger",
    kills: false,
    line: "Every record is hashed into a Merkle chain whose head advances by conditional write. Receipts verify client-side.",
  },
];

const PROOFS = [
  {
    label: "kill switch drill",
    result: "passed",
    date: "2026-09-28",
    line: "One environment flag halted every gate through the public URL (503 kernel-halted). Revert restored service.",
  },
  {
    label: "out-of-scope mutation",
    result: "rejected",
    date: "2026-09-28",
    line: "A foreign-table delete denied at the gate by GATE-ARN-001. The IAM reach ends at three sandbox resources; the test is CI-gated.",
  },
  {
    label: "rollback",
    result: "byte-identity verified",
    date: "2026-09-27",
    line: "A gated deletion executed against live state, then reversed from the TTL vault. The restored item hashed identical to the pre-capture image.",
  },
  {
    label: "budget",
    result: "usd 10 cap, under usd 2 spent",
    date: "continuous",
    line: "A live cost budget alarms the account. ARM64 compute, on-demand DynamoDB, free-tier CloudFront: no always-on burn.",
  },
];

const STACK = [
  ["Lambda (ARM64, Python 3.12)", "gate, quorum, probes, saga, ledger handlers"],
  ["API Gateway (regional)", "eleven routes, stage throttle 10 rps / burst 20"],
  ["Amazon Bedrock", "Nova Pro + Llama 3.3 70B quorum, Nova Lite perimeter"],
  ["DynamoDB (2 tables, SSE)", "single-table decisions + demo ledger, dual-write"],
  ["KMS HMAC_256", "single-use bypass token signing"],
  ["Step Functions + EventBridge", "deep path, decision and incident events"],
  ["S3 + CloudFront", "this site, /v1/* same-origin proxy, evidence archive"],
  ["CloudWatch, X-Ray, CloudTrail", "metrics, traces, the agent's own audit trail"],
];

function TerminalStage({ index, detail, hostile = false }: { index: string; detail: string; hostile?: boolean }) {
  return (
    <div className="grid grid-cols-[26px_minmax(0,1fr)] gap-2 border-b border-coalline py-1.5 last:border-b-0">
      <span className="mono text-[10px] leading-5 text-fog">{index}</span>
      <span className={`mono break-words text-[11px] leading-5 ${hostile ? "text-antares" : "text-stone"}`}>
        {detail}
      </span>
    </div>
  );
}

function VerdictTerminal() {
  const v = RECORDED_VERDICT;
  const q = v.quorum!;
  return (
    <figure className="w-full">
      <div className="border border-inkw/80 bg-coal shadow-[0_24px_60px_-24px_rgba(25,21,17,0.45)]">
        <div className="flex items-center justify-between border-b border-coalline px-5 py-3">
          <span className="mono text-[10px] uppercase tracking-[0.18em] text-fog">
            verdict · recorded from the live kernel
          </span>
          <span className="mono text-[10px] text-fog">{v.ts.slice(0, 10)}</span>
        </div>

        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-coalline px-5 py-4">
          <div className="flex items-baseline gap-3">
            <span className="mono text-3xl text-antares">{v.state}</span>
            <span className="mono text-[10px] text-fog">{q.fusion}</span>
          </div>
          <span className="mono text-[10px] text-fog">
            {v.latency_ms.total} ms total · gate {v.latency_ms.gate} ms · quorum {q.quorum_ms} ms
          </span>
        </div>

        <div className="grid gap-0 px-5 py-3 sm:grid-cols-2">
          <div className="sm:border-r sm:border-coalline sm:pr-4">
            <TerminalStage index="01" hostile detail={`OVR-001 · ${q.perimeter_findings![0].detail.slice(11)}`} />
            <TerminalStage index="02" detail={`gate: class ${v.gate.action_class} · GATE-CLS-001`} />
            <TerminalStage
              index="03"
              detail={`llama-3.3-70b risk ${q.votes.adversary.risk} (exfiltration) vs nova-pro risk ${q.votes.reasoner.risk}`}
            />
          </div>
          <div className="sm:pl-4">
            <TerminalStage index="04" detail={`radius: 1 at risk · weight 0.3 · reversibility 0.6 → score 0.12`} />
            <TerminalStage index="05" detail="human signature: not reached, convicted upstream" />
            <TerminalStage index="06" detail={`evidence bundle ${v.verdict_id.slice(0, 16)}…`} />
          </div>
        </div>

        <div className="grid gap-px border-t border-coalline bg-coalline sm:grid-cols-2">
          <div className="bg-coal px-5 py-4">
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">
              adversary · llama-3.3-70b
            </p>
            <p className="mono mt-1 text-2xl text-paper">{q.votes.adversary.risk}</p>
            <p className="mono text-[10px] text-antares">{q.votes.adversary.threat_vector}</p>
            <p className="mt-2 text-xs leading-relaxed text-stone">{q.votes.adversary.reason}</p>
          </div>
          <div className="bg-coal px-5 py-4">
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">reasoner · nova-pro</p>
            <p className="mono mt-1 text-2xl text-paper">{q.votes.reasoner.risk}</p>
            <p className="mono text-[10px] text-fog">blast radius judgment</p>
            <p className="mt-2 text-xs leading-relaxed text-stone">{q.votes.reasoner.reason}</p>
          </div>
        </div>

        <p className="mono border-t border-coalline px-5 py-3 text-[10px] leading-relaxed text-fog">
          canary {q.votes.audit_ref} planted in every quorum prompt: a model that repeats it is
          convicted on the spot. tokens {q.usage.input} in / {q.usage.output} out.
        </p>
      </div>
      <figcaption className="mono mt-3 text-[11px] text-fog">
        one dispatch, recorded 2026-09-28: a poisoned write carrying OWASP LLM01.{" "}
        <Link href="/console" className="text-ember underline hover:text-inkw">
          replay it live on the console
        </Link>
      </figcaption>
    </figure>
  );
}

export default function LandingV2() {
  return (
    <div className="min-h-screen bg-paper text-inkw">
      <header className="border-b border-paperline">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-4">
            <span className="mono text-sm tracking-[0.32em] text-ember">ANTARES</span>
            <span className="mono hidden text-[10px] uppercase tracking-[0.18em] text-fog sm:inline">
              execution governor for autonomous agents
            </span>
          </div>
          <nav className="mono flex items-center gap-5 text-xs">
            <Link href="/console" className="text-inkw hover:text-ember">console</Link>
            <a href="#benchmark" className="text-stone hover:text-inkw">benchmark</a>
            <a href="https://github.com/Prakhar2025/Antares" target="_blank" rel="noreferrer" className="text-stone hover:text-inkw">
              github
            </a>
            <Link href="/" className="text-fog hover:text-inkw" title="the earlier design, kept for comparison">v1</Link>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6">
        {/* hero: statement left, the machine right */}
        <section className="grid gap-12 py-16 lg:grid-cols-12 lg:gap-10 lg:py-20">
          <div className="lg:col-span-5">
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-ember">
              live on aws · us-east-1 · zero login
            </p>
            <h1 className="serif-display mt-6 text-[44px] leading-[1.05] sm:text-[56px]">
              Every tool call an agent makes, judged before it executes.
            </h1>
            <p className="mt-6 max-w-md text-[17px] leading-relaxed text-stone">
              Antares stands between your agents and your cloud. Deterministic code
              vetoes first, a cross-vendor model quorum judges what code cannot,
              blast radius is measured from live state, and every mutation is
              reversible by construction.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Link
                href="/console"
                className="mono bg-inkw px-6 py-3.5 text-xs tracking-[0.18em] text-paper transition-colors hover:bg-ember"
              >
                OPEN THE CONSOLE
              </Link>
              <a href="#benchmark" className="mono text-xs tracking-[0.14em] text-stone underline hover:text-inkw">
                read the benchmark
              </a>
            </div>
            <p className="mono mt-8 text-[11px] text-fog">models propose, code decides.</p>
          </div>
          <div className="lg:col-span-7">
            <VerdictTerminal />
          </div>
        </section>
      </div>

      <LiveTicker />

      <div className="mx-auto max-w-7xl px-6">
        {/* the editorial statement */}
        <section className="grid gap-10 py-20 lg:grid-cols-12">
          <h2 className="serif-display max-w-xl text-4xl leading-[1.12] lg:col-span-7">
            Between a model&rsquo;s decision and your cloud there is nothing.
          </h2>
          <div className="lg:col-span-4 lg:col-start-9">
            <p className="text-[15px] leading-relaxed text-stone">
              Text guardrails read content strings. IaC scanners read code. Posture
              tools read configuration. None of them governs the moment an agent&rsquo;s
              thought becomes a live AWS mutation. That choke point was unoccupied.
              Antares occupies it.
            </p>
          </div>
          <div className="grid gap-px border border-paperline bg-paperline sm:grid-cols-3 lg:col-span-12">
            {[
              ["01", "prompt injection is risk #1", "OWASP ranks untrusted text carrying hidden instructions first in its Top 10 for LLM applications."],
              ["02", "guards read the wrong layer", "content scanners never see tool parameters, resource ARNs, or the state a deletion would destroy."],
              ["03", "one call is the whole loss", "a single injected or hallucinated mutation destroys state that took months to build. Recovery without a pre-captured image is archaeology."],
            ].map(([id, head, body]) => (
              <div key={id} className="bg-paper p-6">
                <p className="mono text-[11px] text-ember">{id}</p>
                <p className="mt-2 text-sm font-medium">{head}</p>
                <p className="mt-2 text-[13px] leading-relaxed text-stone">{body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* the kill spine */}
        <section className="grid gap-10 border-t border-paperline py-20 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">the pipeline</p>
            <h2 className="serif-display mt-4 text-4xl leading-[1.12]">How a call dies.</h2>
            <p className="mt-5 text-[15px] leading-relaxed text-stone">
              Six stages, four of them lethal. A call that survives all six carries a
              receipt whose hash chain anyone can verify.
            </p>
            <p className="mono mt-6 text-[11px] leading-relaxed text-fog">
              <span className="text-ember">filled nodes</span> can kill a call.{" "}
              <span className="text-stone">hollow nodes</span> measure and record.
            </p>
          </div>
          <div className="lg:col-span-7 lg:col-start-6">
            <ol>
              {KILL_SPINE.map((stage, i) => (
                <li key={stage.id} className="relative grid grid-cols-[32px_1fr] gap-4 pb-8 last:pb-0">
                  {i < KILL_SPINE.length - 1 && (
                    <span className="absolute left-[7px] top-4 h-full w-px bg-paperline" aria-hidden />
                  )}
                  <span
                    className={`mt-1.5 h-[15px] w-[15px] rounded-full border-2 ${
                      stage.kills ? "border-ember bg-ember" : "border-stone bg-paper"
                    }`}
                  />
                  <div>
                    <p className="text-[15px] font-medium">
                      <span className="mono mr-3 text-xs text-fog">{stage.id}</span>
                      {stage.name}
                    </p>
                    <p className="mt-1.5 max-w-xl text-[13px] leading-relaxed text-stone">{stage.line}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>
      </div>

      {/* the dark band: benchmark, inverted */}
      <section id="benchmark" className="bg-coal text-paper">
          <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="grid gap-10 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">
                300-case corpus · 4 candidates · measured 2026-09-27
              </p>
              <h2 className="serif-display mt-4 text-4xl leading-[1.12]">
                The adversary seat is decided by data, not preference.
              </h2>
              <p className="mt-5 max-w-md text-[15px] leading-relaxed text-stone">
                Same-family models share blind spots, so the red-team seat goes to a
                family with zero shared lineage with the Nova reasoner. Every
                candidate ran the full corpus with identical prompts and thresholds.
              </p>
            </div>
            <div className="lg:col-span-7">
              <BenchmarkTable />
              <div className="mt-8 border-l-2 border-antares pl-5">
                <p className="mono text-[11px] uppercase tracking-[0.16em] text-antares">the miss we publish</p>
                <p className="mt-2 max-w-lg text-[13px] leading-relaxed text-stone">
                  Benign FPR measured 0.193 against a 0.035 target. The misses
                  concentrate in the adversarial-benign slice: the red-teamer is
                  instructed to assume malice and over-flags quoted attack grammar in
                  benign security prose. The regression is named, the fix path is
                  scheduled, the corpus is versioned. A benchmark that only publishes
                  wins is marketing.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6">
        {/* proof stamps */}
        <section className="border-t border-paperline py-20">
          <div className="flex items-baseline justify-between">
            <h2 className="serif-display text-4xl leading-[1.12]">Proof over promises.</h2>
            <span className="mono hidden text-[10px] uppercase tracking-[0.18em] text-fog sm:inline">
              exercised live, dated
            </span>
          </div>
          <div className="mt-10 grid gap-px border border-paperline bg-paperline sm:grid-cols-2 lg:grid-cols-4">
            {PROOFS.map((proof) => (
              <div key={proof.label} className="bg-paper p-6">
                <p className="mono text-[10px] uppercase tracking-[0.16em] text-fog">{proof.label}</p>
                <p className="mono mt-2 text-sm text-moss">{proof.result}</p>
                <p className="mt-3 text-[13px] leading-relaxed text-stone">{proof.line}</p>
                <p className="mono mt-4 text-[10px] text-fog">{proof.date}</p>
              </div>
            ))}
          </div>
        </section>

        {/* the stack */}
        <section className="border-t border-paperline py-20">
          <div className="flex items-baseline justify-between">
            <h2 className="serif-display text-4xl leading-[1.12]">The stack, as deployed.</h2>
            <span className="mono hidden text-[10px] uppercase tracking-[0.18em] text-fog sm:inline">
              every service earns its place
            </span>
          </div>
          <div className="mt-10 grid gap-x-14 sm:grid-cols-2">
            {STACK.map(([service, role]) => (
              <div key={service} className="flex items-baseline justify-between gap-4 border-b border-paperline py-3">
                <span className="mono text-xs text-inkw">{service}</span>
                <span className="text-right text-[11px] text-stone">{role}</span>
              </div>
            ))}
          </div>
        </section>

        {/* built in the open */}
        <section className="border-t border-paperline py-20">
          <div className="grid gap-10 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <h2 className="serif-display text-4xl leading-[1.12]">Built in the open.</h2>
              <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-stone">
                Antares is the fourth link in a chain built around one question: what
                happens when a model is wrong and money moves. TruthLayer verifies
                what AI claims. Gatehouse gates scam decisions with hash-chained
                evidence. Sentinel scores cross-merchant fraud deterministically.
                Antares governs the agents themselves.
              </p>
              <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-stone">
                Built end to end by a coding agent connected to AWS, reviewed at every
                milestone gate by Prakhar Shukla. The agent&rsquo;s own CloudTrail calls
                are the build record; the what-broke ledger carries every failure with
                its prevention rule. Nineteen design documents, one failure ledger,
                zero undocumented decisions.
              </p>
            </div>
            <div className="mono space-y-2 self-end text-xs text-stone lg:col-span-4 lg:col-start-9">
              <p>2 IEEE publications on deepfake detection</p>
              <p>top 50 global finalist · aws aiideas</p>
              <p>national winner · sbi youth ideathon, iit delhi</p>
              <p className="text-inkw">prakhar shukla · nagpur, india</p>
            </div>
          </div>
        </section>
      </div>

      <footer className="border-t border-paperline">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <span className="mono text-[11px] text-fog">models propose, code decides</span>
          <span className="mono text-[11px] text-fog">
            antares-dev namespace · us-east-1 ·{" "}
            <Link href="/archive" className="underline hover:text-inkw">compare with v1</Link>
          </span>
        </div>
      </footer>
    </div>
  );
}

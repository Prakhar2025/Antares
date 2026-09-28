"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { gateCall, type Verdict } from "@/lib/api";
import { PRESETS, type Preset } from "@/lib/presets";
import { RECORDED_VERDICT } from "@/lib/recorded";

function shortModel(id: string | undefined): string {
  if (!id) return "n/a";
  if (id.includes("llama3-3")) return "llama-3.3-70b";
  if (id.includes("llama4")) return "llama-4-maverick";
  if (id.includes("gpt-oss")) return "gpt-oss-120b";
  if (id.includes("deepseek")) return "deepseek-r1";
  if (id.includes("nova-pro")) return "nova-pro";
  if (id.includes("nova-lite")) return "nova-lite";
  return id.slice(0, 22);
}

const STATE_TONE: Record<string, string> = {
  ALLOW: "text-allow",
  HARD_BLOCK: "text-antares",
  ABSTAIN: "text-abstain",
};

type StageStatus = "done" | "active" | "skip" | "wait";

function Dot({ status, tone = "bg-paper" }: { status: StageStatus; tone?: string }) {
  if (status === "active") return <span className="mt-1 inline-block h-2 w-2 animate-pulse rounded-full bg-abstain" />;
  if (status === "done") return <span className={`mt-1 inline-block h-2 w-2 rounded-full ${tone}`} />;
  return <span className="mt-1 inline-block h-2 w-2 rounded-full bg-coalline" />;
}

function StageRow({
  index,
  name,
  status,
  tone,
  detail,
}: {
  index: string;
  name: string;
  status: StageStatus;
  tone?: string;
  detail?: string;
}) {
  return (
    <div className="grid grid-cols-[26px_132px_16px_1fr] items-start gap-3 border-b border-coalline py-3 last:border-b-0">
      <span className="mono pt-0.5 text-[10px] text-fog">{index}</span>
      <span className={`text-[13px] font-medium ${status === "wait" ? "text-fog" : "text-paper"}`}>
        {name}
      </span>
      <Dot status={status} tone={tone} />
      <span className="mono text-[11px] leading-relaxed text-stone">{detail ?? ""}</span>
    </div>
  );
}

function Pipeline({ v, live }: { v: Verdict; live: boolean }) {
  const q = v.quorum;
  const radius = v.radius;
  const perimeterFindings = q?.perimeter_findings ?? [];
  const gateRules = v.gate.findings.map((f) => f.rule_id);
  const blocked = v.state === "HARD_BLOCK";
  const abstained = v.state === "ABSTAIN";

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-coalline pb-5">
        <div className="flex items-baseline gap-4">
          <span className={`mono text-[40px] leading-none ${STATE_TONE[v.state]}`}>{v.state}</span>
          {q && <span className="mono text-[11px] text-fog">{q.fusion}</span>}
        </div>
        <span className="mono text-[11px] text-fog">
          {v.latency_ms.total} ms total · gate {v.latency_ms.gate} ms
          {q ? ` · quorum ${q.quorum_ms} ms` : ""}
        </span>
      </div>

      <div className="mt-2">
        <StageRow
          index="01"
          name="Perimeter"
          status="done"
          tone={perimeterFindings.length ? "bg-antares" : "bg-paper"}
          detail={
            perimeterFindings.length
              ? perimeterFindings.map((f) => `${f.rule_id}: ${f.detail}`).join("  ·  ")
              : "clean: no attack grammar in parameters"
          }
        />
        <StageRow
          index="02"
          name="Deterministic gate"
          status="done"
          tone={v.gate.code_blocked ? "bg-antares" : "bg-paper"}
          detail={
            v.gate.code_blocked
              ? `VETO: ${gateRules.join(", ")}. No model was consulted`
              : `class ${v.gate.action_class} · ${gateRules.join(", ") || "no findings"}`
          }
        />
        <StageRow
          index="03"
          name="Cross-vendor quorum"
          status={q ? "done" : "skip"}
          tone={blocked ? "bg-antares" : "bg-paper"}
          detail={
            q
              ? `${shortModel(q.votes.adversary.model)} risk ${q.votes.adversary.risk} (${q.votes.adversary.threat_vector ?? "n/a"}) vs ${shortModel(q.votes.reasoner.model)} risk ${q.votes.reasoner.risk} · divergence ${q.divergence}`
              : "not escalated: read-class, gate-clean"
          }
        />
        <StageRow
          index="04"
          name="State probes"
          status={radius ? "done" : "skip"}
          detail={
            radius
              ? `${radius.resources_at_risk} at risk · weight ${radius.severity_weight} · reversibility ${radius.reversibility} → score ${radius.score}${radius.unknown ? " (UNKNOWN → max severity)" : ""}`
              : "no mutation proposed"
          }
        />
        <StageRow
          index="05"
          name="Human signature"
          status={abstained ? "active" : "skip"}
          detail={
            abstained
              ? "ABSTAIN: a KMS-signed, single-use, 60-second bypass token was issued for this verdict"
              : blocked
                ? "not reached: convicted upstream"
                : "not required"
          }
        />
        <StageRow
          index="06"
          name="Provenance"
          status="done"
          tone="bg-paper"
          detail={`evidence bundle ${v.verdict_id}`}
        />
      </div>
    </div>
  );
}

function Evidence({ v, live }: { v: Verdict; live: boolean }) {
  const q = v.quorum;
  return (
    <div>
      <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">
        evidence · {live ? "live dispatch" : "recorded 2026-09-28"}
      </p>

      {q ? (
        <div className="mt-4 space-y-px bg-coalline">
          <div className="bg-coal p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-fog">
              adversary · {shortModel(q.votes.adversary.model)}
            </p>
            <p className="mono mt-1 text-3xl text-paper">{q.votes.adversary.risk ?? "n/a"}</p>
            <p className="mono mt-0.5 text-[10px] text-antares">{q.votes.adversary.threat_vector ?? "n/a"}</p>
            <p className="mt-2 text-xs leading-relaxed text-stone">
              {q.votes.adversary.reason ?? "no rationale returned"}
            </p>
          </div>
          <div className="bg-coal p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-fog">
              reasoner · {shortModel(q.votes.reasoner.model)}
            </p>
            <p className="mono mt-1 text-3xl text-paper">{q.votes.reasoner.risk ?? "n/a"}</p>
            <p className="mono mt-0.5 text-[10px] text-fog">blast radius judgment</p>
            <p className="mt-2 text-xs leading-relaxed text-stone">
              {q.votes.reasoner.reason ?? "no rationale returned"}
            </p>
          </div>
        </div>
      ) : (
        <p className="mono mt-4 text-[11px] leading-relaxed text-stone">
          no quorum on this verdict: the gate decided it without models.
        </p>
      )}

      {q && (
        <p className="mono mt-4 text-[10px] leading-relaxed text-fog">
          canary {q.votes.audit_ref} planted in the data section of every quorum
          prompt: a model that repeats it has obeyed data instead of policy and is
          convicted on the spot. tokens {q.usage.input} in / {q.usage.output} out.
        </p>
      )}

      <details className="mt-5 border border-coalline">
        <summary className="mono cursor-pointer px-4 py-2.5 text-[11px] text-fog hover:text-paper">
          raw verdict json
        </summary>
        <pre className="mono max-h-72 overflow-auto border-t border-coalline p-4 text-[10px] leading-relaxed text-stone">
          {JSON.stringify(v, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export default function ConsoleV2() {
  const [selected, setSelected] = useState<Preset>(PRESETS[2]);
  const [verdict, setVerdict] = useState<Verdict>(RECORDED_VERDICT);
  const [live, setLive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const dispatch = useCallback(async () => {
    setBusy(true);
    setError(null);
    setElapsed(0);
    timer.current = setInterval(() => setElapsed((e) => e + 100), 100);
    try {
      setVerdict(await gateCall(selected.call));
      setLive(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (timer.current) clearInterval(timer.current);
      setBusy(false);
    }
  }, [selected]);

  useEffect(() => {
    document.title = "Antares · kernel console";
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-coal text-paper">
      <header className="border-b border-coalline">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-4">
            <Link href="/v2" className="mono text-sm tracking-[0.32em] text-paper">
              ANTARES
            </Link>
            <span className="mono hidden text-[10px] uppercase tracking-[0.18em] text-fog sm:inline">
              kernel console
            </span>
          </div>
          <div className="mono flex items-center gap-5 text-[11px]">
            <span className="flex items-center gap-2 text-allow">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-allow" />
              connected · us-east-1
            </span>
            <Link href="/console" className="text-fog hover:text-paper" title="the earlier console, kept for comparison">
              v1
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-10 lg:grid-cols-12">
        {/* left: scenarios */}
        <aside className="lg:col-span-3">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-fog">scenarios</p>
          <div className="mt-3 space-y-1.5">
            {PRESETS.map((preset) => {
              const active = selected.id === preset.id;
              return (
                <button
                  key={preset.id}
                  onClick={() => setSelected(preset)}
                  className={`block w-full border px-3.5 py-2.5 text-left transition-colors ${
                    active ? "border-antares/70 bg-paper/5" : "border-coalline hover:border-fog/40"
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-[13px] font-medium leading-snug text-paper">{preset.name}</span>
                    <span
                      className={`mono shrink-0 text-[9px] uppercase tracking-[0.16em] ${
                        preset.tag === "attack"
                          ? "text-antares"
                          : preset.tag === "destroy"
                            ? "text-abstain"
                            : "text-fog"
                      }`}
                    >
                      {preset.tag}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <button
            onClick={dispatch}
            disabled={busy}
            className="mono mt-5 w-full bg-antares py-3.5 text-xs tracking-[0.18em] text-paper transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? `JUDGING · ${elapsed} MS` : "DISPATCH"}
          </button>

          <div className="mt-5 border border-coalline p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-fog">what to expect</p>
            <p className="mt-2 text-xs leading-relaxed text-stone">{selected.expect}</p>
          </div>

          <p className="mono mt-4 text-[10px] leading-relaxed text-fog">
            nothing here is mocked: every dispatch is a real call into the live
            lambda through CloudFront. destructive routes (execute, rollback) require
            an api key and are not exposed here.
          </p>
        </aside>

        {/* center: the pipeline */}
        <section className="lg:col-span-5">
          {error ? (
            <div className="border border-antares/50 p-5">
              <p className="mono text-sm text-antares">{error}</p>
              <p className="mono mt-2 text-[11px] leading-relaxed text-fog">
                local preview serves static files only: the kernel sits behind the
                deployed url, so dispatch there. on the live site this line means the
                10 req/s edge throttle: retry in a moment.
              </p>
            </div>
          ) : busy ? (
            <div>
              <p className="mono text-sm text-abstain">judging · {elapsed} ms elapsed</p>
              <div className="mt-5">
                <StageRow index="01" name="Perimeter" status="active" detail="scanning parameters for attack grammar…" />
                <StageRow index="02" name="Deterministic gate" status="active" detail="schema, shell tokens, namespace, class weight…" />
                <StageRow
                  index="03"
                  name="Cross-vendor quorum"
                  status={selected.id === "benign" ? "skip" : "active"}
                  detail={selected.id === "benign" ? "not escalated: read-class" : "two model families voting in parallel…"}
                />
                <StageRow
                  index="04"
                  name="State probes"
                  status={selected.tag === "read" ? "skip" : "active"}
                  detail={selected.tag === "read" ? "no mutation proposed" : "reading live cloud state…"}
                />
                <StageRow index="05" name="Human signature" status="wait" detail="" />
                <StageRow index="06" name="Provenance" status="wait" detail="" />
              </div>
            </div>
          ) : (
            <Pipeline v={verdict} live={live} />
          )}
        </section>

        {/* right: evidence */}
        <aside className="lg:col-span-4">
          <Evidence v={verdict} live={live} />
        </aside>
      </div>

      <footer className="border-t border-coalline">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <span className="mono text-[10px] text-fog">every verdict carries its evidence bundle id</span>
          <span className="mono text-[10px] text-fog">models propose, code decides</span>
        </div>
      </footer>
    </div>
  );
}

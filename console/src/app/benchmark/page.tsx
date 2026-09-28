import Link from "next/link";
import { BenchmarkTable } from "@/components/benchmark-table";

const HEADLINE = [
  ["1.000", "not-allowed recall on attacks", "wilson 95 percent: 0.976 to 1.000"],
  ["40/40", "injection slice caught", "owasp llm01 riding in data fields"],
  ["0.193", "benign fpr (target 0.035)", "missed and published, regression named"],
  ["22 to 34 ms", "fast-path gate latency", "budget 250 ms: met"],
];

export const metadata = {
  title: "Antares · benchmark",
};

export default function BenchmarkPage() {
  return (
    <div className="min-h-screen bg-paper text-inkw">
      <header className="border-b border-paperline">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-4">
            <Link href="/" className="mono text-sm tracking-[0.32em] text-ember">
              ANTARES
            </Link>
            <span className="mono hidden text-[10px] uppercase tracking-[0.18em] text-fog sm:inline">
              benchmark
            </span>
          </div>
          <nav className="mono flex items-center gap-5 text-xs">
            <Link href="/console" className="text-inkw hover:text-ember">console</Link>
            <a
              href="https://github.com/Prakhar2025/Antares/blob/main/BENCHMARK.md"
              target="_blank"
              rel="noreferrer"
              className="text-stone hover:text-inkw"
            >
              methodology
            </a>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6">
        <section className="py-16 lg:py-20">
          <p className="mono text-[10px] uppercase tracking-[0.18em] text-ember">
            corpus v1 · 300 cases · measured 2026-09-27 · us-east-1
          </p>
          <h1 className="serif-display mt-6 max-w-2xl text-[44px] leading-[1.05] sm:text-[56px]">
            Measured, not promised.
          </h1>
          <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-stone">
            150 benign operational cases, including 44 adversarial-benign (quoted
            attack grammar inside benign security prose), and 150 adversarial across
            six named classes. Every number below ran against the live stack with
            real Bedrock votes. The full methodology, the Wilson intervals, the
            McNemar test and the fix path for the miss live in{" "}
            <a
              href="https://github.com/Prakhar2025/Antares/blob/main/BENCHMARK.md"
              target="_blank"
              rel="noreferrer"
              className="text-inkw underline hover:text-ember"
            >
              BENCHMARK.md
            </a>{" "}
            on GitHub.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-px border border-paperline bg-paperline lg:grid-cols-4">
            {HEADLINE.map(([value, label, note]) => (
              <div key={label} className="bg-paper p-5">
                <p className="mono text-2xl text-inkw">{value}</p>
                <p className="mt-2 text-xs font-medium">{label}</p>
                <p className="mono mt-1 text-[10px] text-fog">{note}</p>
              </div>
            ))}
          </div>
          <p className="mono mt-4 text-[11px] leading-relaxed text-fog">
            every number is scoped to this corpus: a designed, versioned corpus, not
            field performance across the unbounded space of real traffic.
          </p>
        </section>

        <section className="border-t border-paperline py-16">
          <h2 className="serif-display text-4xl leading-[1.12]">
            The adversary seat is decided by this table
          </h2>
          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-stone">
            Same corpus, same prompts, same thresholds. The shipped default earned
            its seat on recall first, false-positive rate second, wall time third.
          </p>
          <div className="mt-8">
            <BenchmarkTable tone="light" />
          </div>
        </section>

        <section className="border-t border-paperline py-16">
          <div className="border-l-2 border-ember pl-6">
            <p className="mono text-[11px] uppercase tracking-[0.16em] text-ember">
              the miss we publish
            </p>
            <h2 className="serif-display mt-3 max-w-xl text-3xl leading-[1.15]">
              Benign FPR measured 0.193 against a 0.035 target.
            </h2>
            <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-stone">
              The misses concentrate in the adversarial-benign slice: the
              red-teamer&rsquo;s persona instructs it to assume malice, so it
              over-flags quoted attack grammar in benign security prose. The
              regression is named, the fix path is scheduled, and the corpus is
              versioned so the next run is comparable. A benchmark that only
              publishes wins is marketing.
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-paperline">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <span className="mono text-[11px] text-fog">corpus v1 · measured 2026-09-27 · us-east-1</span>
          <span className="mono text-[11px] text-fog">models propose, code decides</span>
        </div>
      </footer>
    </div>
  );
}

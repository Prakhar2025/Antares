import Link from "next/link";
import { BenchmarkTable } from "@/components/benchmark-table";

const HEADLINE = [
  ["1.00", "not-allowed recall on attacks", "wilson 95%: 0.976 – 1.000"],
  ["40/40", "injection slice caught", "owasp llm01 riding in data fields"],
  ["0.193", "benign fpr (target 0.035)", "missed and published, regression named"],
  ["22–34 ms", "fast-path gate latency", "budget 250 ms: met"],
];

export const metadata = {
  title: "Antares · benchmark",
};

export default function BenchmarkPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 pb-16">
      <header className="flex items-center justify-between border-b hairline py-5">
        <div className="flex items-center gap-4">
          <Link href="/" className="mono text-base tracking-[0.32em] text-antares">
            ANTARES
          </Link>
          <span className="label hidden sm:inline">benchmark</span>
        </div>
        <Link href="/console" className="mono text-xs text-ink-dim hover:text-ink">
          live console
        </Link>
      </header>

      <section className="py-14">
        <h1 className="text-3xl font-semibold tracking-tight">
          Measured, not promised.
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-dim">
          300-case corpus: 150 benign operational cases including 44
          adversarial-benign (quoted attack grammar inside benign security prose) and
          150 adversarial across six named classes. Every number below ran against the
          live stack with real Bedrock votes. The full methodology, Wilson intervals,
          McNemar test and the published miss live in{" "}
          <a
            href="https://github.com/Prakhar2025/Antares/blob/main/BENCHMARK.md"
            target="_blank"
            rel="noreferrer"
            className="text-ink underline hover:text-antares"
          >
            BENCHMARK.md
          </a>{" "}
          on GitHub.
        </p>
        <div className="mt-10 grid grid-cols-2 gap-px border hairline bg-hairline lg:grid-cols-4">
          {HEADLINE.map(([value, label, note]) => (
            <div key={label} className="bg-void p-5">
              <p className="mono text-2xl text-ink">{value}</p>
              <p className="mt-2 text-xs font-medium">{label}</p>
              <p className="mono mt-1 text-[10px] text-ink-faint">{note}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t hairline py-14">
        <h2 className="text-xl font-semibold tracking-tight">
          The adversary seat is decided by this table
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-dim">
          Same corpus, same prompts, same thresholds. The shipped default earned its
          seat on recall first, false-positive rate second, wall time third.
        </p>
        <div className="mt-8">
          <BenchmarkTable />
        </div>
      </section>

      <section className="border-t hairline py-14">
        <h2 className="text-xl font-semibold tracking-tight">
          The miss we publish
        </h2>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-dim">
          The benign false-positive target was 0.035. Measured: 0.193. The misses
          concentrate in the adversarial-benign slice: the red-teamer&apos;s persona
          instructs it to assume malice, so it over-flags quoted attack grammar in
          benign security prose. A benchmark that only publishes wins is marketing.
          The regression is named, the fix path is scheduled, and the corpus is
          versioned so the next run is comparable.
        </p>
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-4 border-t hairline pt-8 text-xs text-ink-faint">
        <span className="mono">corpus v1 · measured 2026-09-27 · us-east-1</span>
        <span className="mono">models propose, code decides</span>
      </footer>
    </main>
  );
}

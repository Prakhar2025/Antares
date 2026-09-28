"use client";

const ROWS = [
  { model: "Meta Llama 3.3 70B", note: "shipped default", recall: "1.000", hard: "0.700", fpr: "0.193", wall: "133 s" },
  { model: "Meta Llama 4 Maverick", note: "noisy on benign", recall: "0.980", hard: "0.680", fpr: "0.313", wall: "123 s" },
  { model: "OpenAI GPT-OSS 120B", note: "conservative", recall: "0.973", hard: "0.647", fpr: "0.160", wall: "244 s" },
  { model: "DeepSeek R1", note: "5× slower", recall: "0.967", hard: "0.647", fpr: "0.180", wall: "670 s" },
];

export function BenchmarkTable({ tone = "dark" }: { tone?: "dark" | "light" }) {
  const border = tone === "dark" ? "hairline" : "border-paperline";
  const strong = tone === "dark" ? "text-ink" : "text-inkw";
  const dim = tone === "dark" ? "text-ink-dim" : "text-stone";
  const faint = tone === "dark" ? "text-ink-faint" : "text-fog";
  const accent = tone === "dark" ? "text-antares" : "text-ember";
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className={`label border-b ${border}`}>
            <th className="py-2 pr-4 font-normal">adversary</th>
            <th className="py-2 pr-4 font-normal">note</th>
            <th className="py-2 pr-4 font-normal">not-allowed recall</th>
            <th className="py-2 pr-4 font-normal">hard-block recall</th>
            <th className="py-2 pr-4 font-normal">benign fpr</th>
            <th className="py-2 font-normal">wall (300)</th>
          </tr>
        </thead>
        <tbody className="mono text-xs">
          {ROWS.map((row, i) => (
            <tr key={row.model} className={`border-b ${border} ${i === 0 ? strong : dim}`}>
              <td className="py-2.5 pr-4">
                {row.model}
                {i === 0 && <span className={`ml-2 ${accent}`}>✓ shipped</span>}
              </td>
              <td className="py-2.5 pr-4">{row.note}</td>
              <td className="py-2.5 pr-4">{row.recall}</td>
              <td className="py-2.5 pr-4">{row.hard}</td>
              <td className="py-2.5 pr-4">{row.fpr}</td>
              <td className="py-2.5">{row.wall}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={`mt-3 text-[11px] leading-relaxed ${faint}`}>
        300-case corpus (150 benign incl. 44 adversarial-benign, 150 adversarial across
        six classes). Identical prompts and thresholds per candidate. Wilson 95 percent
        intervals and the McNemar comparison against the code-only baseline in
        BENCHMARK.md.
      </p>
    </div>
  );
}

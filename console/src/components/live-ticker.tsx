"use client";

import { useEffect, useState } from "react";

type Metrics = { date: string; counters: Record<string, number> };

/** Four-cell credibility strip under the hero. Live counters when the
 * kernel metrics endpoint is reachable (deployed site); the measured
 * benchmark numbers otherwise (local preview), so the strip never
 * renders a broken-looking state. */
export function LiveTicker() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetch("/v1/metrics")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setMetrics)
      .catch(() => setFailed(true));
  }, []);

  if (failed) {
    return (
      <div className="grid grid-cols-2 gap-px bg-paperline border-y border-paperline lg:grid-cols-4">
        {[
          ["recall 1.000", "not-allowed attacks, 300-case corpus"],
          ["0 hostile passes", "nothing hostile cleared the kernel"],
          ["22 to 34 ms", "fast-path gate latency, measured"],
          ["596 to 940 ms", "escalated path with two model votes"],
        ].map(([value, label]) => (
          <div key={label} className="bg-paper px-5 py-4">
            <p className="mono text-sm text-inkw">{value}</p>
            <p className="mono mt-1 text-[10px] uppercase tracking-[0.14em] text-fog">{label}</p>
          </div>
        ))}
      </div>
    );
  }

  const c = metrics?.counters ?? {};
  const cells = [
    {
      value: c.verdicts != null ? `${c.verdicts} verdicts` : "verdicts",
      label: "issued by the live kernel, counting",
    },
    {
      value: c.state_HARD_BLOCK != null ? `${c.state_HARD_BLOCK} blocked` : "blocked",
      label: "hostile calls convicted, live",
    },
    {
      value: c.state_ABSTAIN != null ? `${c.state_ABSTAIN} abstained` : "abstained",
      label: "passed to a human signature",
    },
    { value: "live", label: "counters from the deployed kernel" },
  ];

  return (
    <div className="grid grid-cols-2 gap-px bg-paperline border-y border-paperline lg:grid-cols-4">
      {cells.map((cell) => (
        <div key={cell.label} className="bg-paper px-5 py-4">
          <p className="mono text-sm text-inkw">{cell.value}</p>
          <p className="mono mt-1 text-[10px] uppercase tracking-[0.14em] text-fog">{cell.label}</p>
        </div>
      ))}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

type Metrics = { date: string; counters: Record<string, number> };

export function LiveCounters() {
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
      <div className="mt-14 border hairline p-5">
        <p className="label mb-2">live counters</p>
        <p className="mono text-xs leading-relaxed text-ink-dim">
          verdicts, allows, blocks and abstentions stream here on the deployed
          site, fetched from the kernel metrics endpoint. the local preview has
          no kernel behind it.
        </p>
      </div>
    );
  }

  const c = metrics?.counters ?? {};
  const cells: { value: string; label: string }[] = [
    { value: c.verdicts != null ? String(c.verdicts) : "n/a", label: "verdicts issued, live" },
    { value: c.state_ALLOW != null ? String(c.state_ALLOW) : "n/a", label: "allowed" },
    { value: c.state_HARD_BLOCK != null ? String(c.state_HARD_BLOCK) : "n/a", label: "hard blocked" },
    { value: c.state_ABSTAIN != null ? String(c.state_ABSTAIN) : "n/a", label: "abstained to human" },
  ];

  return (
    <div className="mt-14 grid grid-cols-2 gap-px border hairline bg-hairline sm:grid-cols-4">
      {cells.map((cell) => (
        <div key={cell.label} className="bg-void p-5">
          <p className="mono text-3xl text-ink">{cell.value}</p>
          <p className="label mt-2">{cell.label}</p>
        </div>
      ))}
    </div>
  );
}

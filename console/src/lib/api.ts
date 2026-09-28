export type Verdict = {
  schema_version: string;
  verdict_id: string;
  state: "ALLOW" | "HARD_BLOCK" | "ABSTAIN";
  call_ref: string;
  gate: {
    code_blocked: boolean;
    action_class: string;
    findings: { rule_id: string; severity: string; category?: string; detail: string }[];
  };
  quorum?: {
    fusion: string;
    divergence: number;
    votes: {
      adversary: { model: string; risk: number | null; threat_vector?: string; reason?: string };
      reasoner: { model: string; risk: number | null; reason?: string };
      audit_ref: string;
    };
    usage: { input: number; output: number };
    quorum_ms: number;
    tripwire: boolean;
    perimeter_findings?: { rule_id: string; detail: string }[];
  } | null;
  radius?: {
    resources_at_risk: number;
    severity_weight: number;
    reversibility: number;
    score: number;
    unknown: boolean;
  } | null;
  latency_ms: { gate: number; quorum: number; probe: number; total: number };
  ts: string;
};

/** Same-origin: the site is served by CloudFront with /v1/* proxied to the
 * regional API, so the console never needs an API url or CORS. */
export async function gateCall(call: unknown): Promise<Verdict> {
  const response = await fetch("/v1/gate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(call),
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => null);
    throw new Error(problem?.detail ?? `gate failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchMetrics(): Promise<{
  date: string;
  counters: Record<string, number>;
}> {
  const response = await fetch("/v1/metrics");
  if (!response.ok) throw new Error(`metrics failed: ${response.status}`);
  return response.json();
}

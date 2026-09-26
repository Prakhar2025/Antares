# Doc 05: Agent Contracts

Version 0.1 · Status: Draft · 2026-09-27

The kernel is only as strong as its contracts. This document is the enforceable specification every integrating agent, every registered tool, and every verdict must satisfy. Where a contract and an implementation disagree, the implementation is defective.

## 1. The integration contract (how agents attach)

An agent never calls AWS directly for gated classes. It calls the kernel:

```
verdict = kernel.gate(tool_call, context)
if verdict.state == ALLOW:    result = kernel.execute(verdict)   # kernel performs the call
elif verdict.state == ABSTAIN: ... handle suspension / bypass ...
else:                          ... act on verdict.diagnosis ...   # machine-readable
```

Contract terms: the agent cannot register a tool whose class is gated and then call around the kernel; the execute path exists only on an ALLOW verdict id; replaying a verdict id is single-use and detected.

## 2. ToolCall schema (versioned, strict)

```
ToolCall {
  call_id:        uuid          # agent-supplied, idempotency key
  tool:           enum          # registered tool name, exact match
  action:         string        # e.g. "dynamodb:UpdateItem"
  params:         object        # validated against the tool's Pydantic schema
  session: {
    session_id:   uuid
    trust_score:  float         # S0 perimeter history for this session
    perimeter:    [finding_id]  # S0 findings attached to this session's inputs
  }
  requested_by:   string        # agent identity
}
```

A ToolCall that fails schema validation is rejected before any model or probe runs. Registration of a tool requires: action class mapping, parameter schema, ARN template, and declared mutability class (READ, WRITE, PERMISSION, DESTROY).

## 3. Verdict schema

```
Verdict {
  verdict_id:     uuid
  state:          enum { ALLOW, HARD_BLOCK, ABSTAIN }
  call_ref:       uuid
  gate: {
    code_blocked: bool
    findings:     [{rule_id, detail}]
    action_class: enum {READ, WRITE, PERMISSION, DESTROY}
  }
  quorum: {                     # present on escalated calls only
    radius_vote:   {model, score, rationale_hash}
    adversary_vote:{model, score, threat_vector, rationale_hash}
    disagreement:  float        # variance across risk scalars, doc 07
    fusion:        string       # the exact deterministic rule that fired
  }
  radius: {                      # present for mutating calls
    resources_at_risk: int
    severity_weight:   float
    reversibility:     float
    score:             float
    inputs:            [{probe, resource, observed_value}]
  }
  bypass: {token_hash, expires_at, single_use: true}   # ABSTAIN only
  merkle_root:    string        # receipt chain root at decision time
  latency_ms:     {gate, quorum, probe, total}
}
```

## 4. Fusion rules (deterministic, published, test-covered)

1. Code gate BLOCK: final, models are never invoked. No quorum can overturn.
2. Action class DESTROY or PERMISSION: always escalated to quorum regardless of code gate.
3. Quorum BLOCK on an escalated call requires: adversary score above the block threshold AND the code gate classifies the call as non-READ. A model may never block a pure read.
4. Disagreement above the escalation threshold: ABSTAIN (human or policy decides), never an average.
5. Radius score above the policy ceiling: HARD_BLOCK regardless of votes.
6. Every rule that fires is named in `verdict.quorum.fusion`. An unnamed rule firing is a defect.

## 5. Bypass token contract

Issued only on ABSTAIN. Signed (KMS), single-use, 60-second expiry, bound to `verdict_id` and `call_id`. Approval records the approving principal in the ledger. A stolen token is dead in 60 seconds and usable once. Bypass usage is itself a ledger event and appears in the incident feed.

## 6. The closed-inputs rule (injection safety by construction)

No registered tool accepts raw untrusted document content as a parameter. Documents pass through S0 perimeter screening first; the kernel passes findings, never raw payloads, into session context. This is the same discipline the author shipped in Gatehouse: a tool that never receives hostile free text cannot be instructed by it.

## 7. Event contracts (EventBridge)

```
antares.decision v1: {verdict_id, state, action_class, radius.score, latency_ms, merkle_root}
antares.incident  v1: {incident_id, kind: TRIPWIRE_FIRE | HARD_BLOCK | BYPASS_USED | ROLLBACK, refs, ts}
```

## 8. Error contract

All API errors are RFC 7807 problem+json with a registered error code (doc 13 registry). A kernel error never leaks stack traces or account identifiers.

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-09-27 | Initial draft for owner review. |

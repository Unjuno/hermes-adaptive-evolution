# Hermes Replay Schema

This document defines the minimum portable event contract used by the Organization State Estimator. It is intentionally narrower than a full Hermes trace.

## Capture bundle

Schema `adaptive-evolution.capture-bundle.v0.2` contains:

```text
manifest.json
sanitized-raw-events.jsonl
normalized-events.jsonl
```

The SQLite database is not portable research input. The sanitized raw stream is the reproducibility boundary for normalization/corruption experiments; the normalized stream is a checksummed derived view.

## Canonical event

Representative normalized event:

```json
{
  "seq": 17,
  "observed_at_ns": 1787140000000000000,
  "hook": "post_tool_call",
  "event_key": "...",
  "session_id": "child-session",
  "task_id": "task-1",
  "turn_id": "turn-3",
  "agent_id": "subagent:child-7",
  "parent_agent_id": null,
  "kind": "tool_result",
  "data": {
    "tool_name": "python",
    "status": "success"
  }
}
```

`observed_at_ns` is observer receive time, not a claim about provider-side event time. It is retained so E3 can compare fixed windows, elapsed-time decay, and change detection.

## Interaction/topology channel

Representative interaction event:

```json
{
  "hook": "subagent_start",
  "parent_agent_id": "root:session-a",
  "agent_id": "subagent:child-7",
  "task_id": "task-1",
  "turn_id": "turn-3"
}
```

Direction is preserved. `parent -> child` is a sample of an operational transition process, not an undirected graph edge.

From counts `C_ij`, the estimator forms a row-normalized empirical operator `P_ij`. Current diagnostics include a directed diffusivity proxy derived from the nontrivial spectrum of `P`.

## Functional-role channel

Role is a posterior inferred from tool/action emissions. Current coarse role families are:

- research;
- implementation;
- verification;
- coordination.

These are experimental macro-states and must be falsified on real traces.

### Role uncertainty and mixing

Missing role evidence is not converted into an artificial cross-role signal. Each agent gets a normalized role-posterior entropy and a derived confidence. Role mixing is computed only through confidence-weighted interaction traffic.

The state therefore reports both:

- `traffic_weighted_role_mixing`;
- `role_conditioned_traffic_coverage`.

Mixing may be `null` when role evidence is insufficient. Low role-conditioned coverage is a reason to fall back, not a reason to substitute a prior mean as if it were measured organization structure.

## Policy/outcome channel

Tool failures, API errors, blocked tasks, and later verified task outcomes contribute to policy/agent fragility and recovery evidence.

This channel must not be the only topology sensor: policy heterogeneity can confound behavior and create false topology inference.

## Identity rule

Strong Hermes correlation IDs are used when available.

Evidence priority:

1. explicit child-session/subagent mapping from `subagent_start`;
2. explicit parent session from a root delegation edge;
3. explicit non-`subagent` session platform;
4. otherwise `session:<id>` uncertainty.

A session-start event with missing platform is not sufficient root evidence. Explicit child evidence overrides any weaker session-start hint.

Current Hermes start/stop payloads are not assumed symmetric: `child_session_id` is sufficient to correlate a stop with a previously observed child.

## Measurement windows

Identity is resolved against the complete available history before a recent measurement window is selected. A short state window must not erase the older `subagent_start` event that established child identity.

Different state variables may ultimately require different timescales; v0.2 exposes a generic recent-event window only as an experiment tool, not as a production memory policy.

## Privacy rule

The recorder is metadata-first. Prompt text, child goals, tool args/results, API bodies, error text, and common secret fields are omitted/redacted **before SQLite persistence** by default.

## Replay diagnostics

Every replay reports at least:

- raw event count;
- unique event count;
- duplicates removed;
- known child/root sessions;
- unattributed observer events;
- uncertain-session events.

E1 additionally reports field-presence fractions without field values. E2 mutates only the pre-sanitized raw event stream so the normalization path can be replayed exactly.

## Authority

Estimator output is `diagnostic_only` until real-Hermes calibration demonstrates that an estimated state variable improves or safely gates a decision. No synthetic event-count threshold authorizes reconfiguration.

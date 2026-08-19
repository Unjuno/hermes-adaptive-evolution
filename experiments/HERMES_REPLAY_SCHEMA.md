# Hermes Replay Schema

This document defines the minimum normalized event contract used by the Organization State Estimator. It is intentionally narrower than a full Hermes trace.

## Interaction/topology channel

Representative normalized event:

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

From counts `C_ij`, the estimator forms a row-normalized empirical operator `P_ij`. Current diagnostics include traffic-weighted role mixing and a directed diffusivity proxy derived from the nontrivial spectrum of `P`.

## Functional-role channel

Representative event:

```json
{
  "hook": "post_tool_call",
  "agent_id": "subagent:child-7",
  "tool_name": "python",
  "status": "success"
}
```

Role is a posterior inferred from tool/action emissions. A lifetime hard role is not assumed.

Current coarse role families are:
- research;
- implementation;
- verification;
- coordination.

These are experimental macro-states and must be falsified on real traces.

## Policy/outcome channel

Tool failures, API errors, blocked tasks, and later verified task outcomes contribute to policy/agent fragility and recovery evidence.

This channel must not be the only topology sensor: policy heterogeneity can confound behavior and create false topology inference.

## Identity rule

Strong Hermes correlation IDs are used when available. Unknown sessions are emitted as explicit uncertain identities such as `session:<id>` rather than being guessed as root agents.

## Privacy rule

The recorder is metadata-first. Prompt text, child goals, tool args/results, API bodies, error text, and common secret fields are omitted/redacted before persistence by default.

## Replay diagnostics

Every replay reports at least:
- raw event count;
- unique event count;
- duplicates removed;
- known child/root sessions;
- unattributed observer events;
- uncertain-session events.

## Authority

Estimator output is `diagnostic_only` until real-Hermes calibration demonstrates that an estimated state variable improves or safely gates a decision. No synthetic event-count threshold authorizes reconfiguration.

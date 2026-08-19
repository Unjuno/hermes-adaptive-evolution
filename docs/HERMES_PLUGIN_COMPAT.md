# Hermes Plugin Compatibility

Checked against `NousResearch/hermes-agent` main commit `13ce0c5c675e843af70d19c9e5144249cd51c8d1` on 2026-08-19.

## Current decision

Use a Hermes general plugin first. Do **not** fork Hermes core unless a live E2E run proves that a decision-relevant correlation/control primitive is unavailable through the public plugin surface.

## Observer hooks used by v0.2

- `on_session_start`
- `on_session_end`
- `on_session_finalize`
- `on_session_reset`
- `post_tool_call`
- `api_request_error`
- `on_skill_lifecycle`
- `subagent_start`
- `subagent_stop`
- `kanban_task_claimed`
- `kanban_task_completed`
- `kanban_task_blocked`

`pre_tool_call`, `pre_api_request`, and successful `post_api_request` are intentionally not registered in the observer slice. The goal is to minimize privacy surface and avoid turning M1/M2 telemetry into a control hook.

## Correlation primitives currently relied on

Where available, the normalizer uses:

- session/task/turn IDs;
- tool-call and API-request IDs;
- parent turn/subagent IDs;
- child session/subagent IDs;
- Kanban run IDs.

Unknown sessions are preserved as uncertain identities; they are never silently promoted to root agents.

## Known boundary

`subagent_start` is an observer event after child construction. It is not treated as a universal pre-agent invocation gate. Earlier blocking of `delegate_task` is possible through `pre_tool_call`, but the observer slice intentionally does not register that directive hook.

## Compatibility rule

Every live-Hermes validation should record:

1. Hermes commit/release;
2. hook field-presence matrix;
3. duplicate/drop/reorder observations;
4. plugin load/install mode;
5. any missing primitive that would change a routing or safety decision.

Only item 5 can justify investigating a fork/core patch.

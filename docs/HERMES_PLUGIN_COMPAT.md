# Hermes Plugin Compatibility

Checked against `NousResearch/hermes-agent` main commit `13ce0c5c675e843af70d19c9e5144249cd51c8d1` on 2026-08-19. The executable contract workflow currently installs released `hermes-agent==0.20.4`; upstream-main compatibility is tracked separately from the release contract.

## Current decision

Use a Hermes general plugin first. Do **not** fork Hermes core unless a live E2E run proves that a decision-relevant correlation/control primitive is unavailable through the public plugin surface.

## Non-interference rule

M1/M2 is a **hook-only observer**. It does not register model-facing tools and therefore does not change the agent's tool schema merely to inspect telemetry. Analysis, export, capture bundling, and replay are external CLI operations.

Directive hooks such as `pre_tool_call` are also intentionally absent from this slice. Observation and later control will be separate capabilities.

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

`pre_tool_call`, `pre_api_request`, and successful `post_api_request` are intentionally not registered. This minimizes privacy surface and avoids turning M1/M2 telemetry into a control path.

## Correlation primitives currently relied on

Where available, the normalizer uses:

- session/task/turn IDs;
- tool-call and API-request IDs;
- parent turn/subagent IDs;
- child session/subagent IDs;
- Kanban run IDs.

Identity inference is conservative:

1. explicit child-session mappings from `subagent_start` are strongest;
2. a `subagent_start.parent_session_id` without a parent subagent establishes a root parent;
3. `on_session_start` is root evidence only when it carries an explicit non-`subagent` platform;
4. missing platform or missing child-start evidence degrades to `session:<id>` uncertainty rather than inventing a root identity.

This is intentionally stricter than a convenience parser because corrupted/missing telemetry is part of E2.

## Upstream subagent asymmetry

Current Hermes `subagent_stop` does not need to repeat `child_subagent_id`; the stop lifecycle can be correlated through `child_session_id`. Hermes's own observability code follows the same pattern. The observer therefore resolves session identity in two passes and does not assume start/stop payload symmetry.

## Known boundary

`subagent_start` is an observer event after child construction. It is not treated as a universal pre-agent invocation gate. Earlier blocking of `delegate_task` is possible through `pre_tool_call`, but the observer slice intentionally does not register that directive hook.

## Executable compatibility gates

The `hermes-contract` workflow performs:

1. `hermes plugins doctor . --ci` against the directory-plugin path;
2. editable installation and `hermes_agent.plugins` entry-point validation;
3. an offline real-Hermes `delegate_task` lifecycle with mocked child execution but real `PluginManager`, lifecycle dispatch, and delegate tool;
4. capture bundle creation;
5. value-free hook field-coverage reporting;
6. duplicate/drop/reorder/optional-ID corruption experiments on the captured event stream;
7. isolated observer write/replay overhead measurement.

The resulting artifact is diagnostic evidence, not a production threshold.

## Compatibility rule

Every provider-backed live-Hermes validation should record:

1. Hermes commit/release;
2. hook field-presence matrix;
3. duplicate/drop/reorder observations;
4. plugin load/install mode;
5. observer overhead;
6. any missing primitive that would change a routing or safety decision.

Only item 6 can justify investigating a fork/core patch.

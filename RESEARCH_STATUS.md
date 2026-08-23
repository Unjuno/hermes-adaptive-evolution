# Research Status — 2026-08-23

The active research branch is `experiment/p0-runtime-closure`.

Start here:

1. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — current architecture and retained findings;
2. [`docs/EXPERIMENT_LEDGER_CURRENT.md`](docs/EXPERIMENT_LEDGER_CURRENT.md) — decision ledger from memory/routing through hard safety and typed tools;
3. [`docs/TYPED_TOOL_TRANSFER_AND_TRANSACTION_BOUNDARY_2026-08-23.md`](docs/TYPED_TOOL_TRANSFER_AND_TRANSACTION_BOUNDARY_2026-08-23.md) — latest completed gate;
4. [`docs/NEXT_ACTIONS.md`](docs/NEXT_ACTIONS.md) — next parser/wire-format gate.

Latest reproducible experiment code:

- [`experiments/typed_tool_transfer.py`](experiments/typed_tool_transfer.py)
- [`experiments/typed_tool_authority_binding.py`](experiments/typed_tool_authority_binding.py)
- [`experiments/typed_tool_tcb_faults.py`](experiments/typed_tool_tcb_faults.py)
- [`experiments/typed_tool_toctou.py`](experiments/typed_tool_toctou.py)

Reproduction commands are in [`results/typed_tools/README.md`](results/typed_tools/README.md).

## Current decision

The mock typed-tool gate is conditionally passed. The architecture currently requires more than a typed schema:

```text
strict decoding
  -> authoritative security binding
  -> current/fresh policy state
  -> commit binding / anti-TOCTOU
  -> certified fallback
  -> local hold
  -> independent capability suspension
```

The next gate attacks the serialized decoder itself: duplicate/unknown fields, coercion, NaN/Inf/overflow, unit ambiguity, schema-version mismatch, Unicode/confusable tool names, actor-injected security fields, and replayed capability tokens.

Only after this boundary passes should the synthetic proposer be replaced by a frozen/live LLM over mock tools.

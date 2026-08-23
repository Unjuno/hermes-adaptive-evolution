# Research Status — 2026-08-23

The active research branch is `experiment/p0-runtime-closure`.

Start here:

1. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — current architecture and retained findings;
2. [`docs/EXPERIMENT_LEDGER_CURRENT.md`](docs/EXPERIMENT_LEDGER_CURRENT.md) — decision ledger;
3. [`docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md`](docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md) — latest completed gate;
4. [`docs/NEXT_ACTIONS.md`](docs/NEXT_ACTIONS.md) — next frozen/live LLM proposer gate.

Latest reproducible experiment code:

- [`experiments/serialized_tool_parser_boundary.py`](experiments/serialized_tool_parser_boundary.py)
- [`experiments/typed_tool_transfer.py`](experiments/typed_tool_transfer.py)
- [`experiments/typed_tool_authority_binding.py`](experiments/typed_tool_authority_binding.py)
- [`experiments/typed_tool_tcb_faults.py`](experiments/typed_tool_tcb_faults.py)
- [`experiments/typed_tool_toctou.py`](experiments/typed_tool_toctou.py)

Latest compact result:

- [`results/parser/parser_boundary_v15_summary.json`](results/parser/parser_boundary_v15_summary.json)

## Current decision

The serialized parser gate is conditionally passed. The current runtime boundary is:

```text
bounded serialized proposal
  -> object/array-distinguishing strict parse
  -> duplicate/unknown field policy
  -> exact schema + tool identity
  -> exact decimal/fixed-precision checks
  -> explicit canonicalization only
  -> authoritative security binding
  -> token freshness / replay prevention
  -> commit binding / anti-TOCTOU
  -> certified fallback
  -> local hold
  -> independent capability suspension
```

Important negative results retained from v15:

- permissive raw JSON forwarding leaked unsafe calls under parser/units/version differentials;
- strict schema alone still failed replay because schema validity is not authorization freshness;
- binary float can hide values slightly above hard decimal bounds;
- an early object/array representation bug caused parser crashes and was invalidated; after the fix, 100,000 random malformed JSON values produced zero uncaught parser exceptions.

The next gate replaces only the synthetic proposer with a frozen/live LLM over mock tools. The model remains outside parsing, authority, freshness, commit, fallback, and suspension.

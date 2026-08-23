# Typed-tool experiment results

Raw v14 JSON outputs are intentionally not committed in this sync because the combined files are about 1.9 MB and include per-seed rows. The committed report contains the retained aggregate results and confidence intervals; the scripts below regenerate the raw outputs.

Run from the repository root.

## Main typed-tool transfer

```bash
python experiments/typed_tool_transfer.py \
  --seeds 64 \
  --scenario all \
  --out results/typed_tools/typed_tool_transfer_64.json
```

## Authority binding

Manipulation/drift/root-outage condition:

```bash
python experiments/typed_tool_authority_binding.py \
  --seeds 64 \
  --manip-p 0.25 \
  --shift 180 \
  --outage 60 \
  --out results/typed_tools/typed_tool_authority_binding_64.json
```

Clean control:

```bash
python experiments/typed_tool_authority_binding.py \
  --seeds 64 \
  --manip-p 0 \
  --shift 180 \
  --outage 60 \
  --out results/typed_tools/typed_tool_authority_binding_clean64.json
```

## Terminal TCB faults

```bash
python experiments/typed_tool_tcb_faults.py \
  --seeds 64 \
  --scenario combined \
  --out results/typed_tools/typed_tool_tcb_faults_64.json
```

## TOCTOU / transaction boundary

Low contention:

```bash
python experiments/typed_tool_toctou.py \
  --seeds 64 \
  --race-p 0.05 \
  --reservation-cost 0.002 \
  --out results/typed_tools/typed_tool_toctou_.05_64.json
```

Intermediate contention:

```bash
python experiments/typed_tool_toctou.py \
  --seeds 64 \
  --race-p 0.18 \
  --reservation-cost 0.002 \
  --out results/typed_tools/typed_tool_toctou_.18_64.json
```

High contention:

```bash
python experiments/typed_tool_toctou.py \
  --seeds 64 \
  --race-p 0.35 \
  --reservation-cost 0.002 \
  --out results/typed_tools/typed_tool_toctou_.35_64.json
```

## Interpretation source

See [`docs/TYPED_TOOL_TRANSFER_AND_TRANSACTION_BOUNDARY_2026-08-23.md`](../../docs/TYPED_TOOL_TRANSFER_AND_TRANSACTION_BOUNDARY_2026-08-23.md).

The reported zero-leak results are conditional on the modeled trusted registry/version state/capability-cut primitives being correct; they are not unconditional real-world safety guarantees.

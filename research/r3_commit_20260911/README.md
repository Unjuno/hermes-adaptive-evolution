# R3 commit policy / dynamics belief separation — 2026-09-11

## Scope

This branch records a synthetic/offline R3 study plus the research-to-plugin maturity boundary. It does not run a real Hermes/LLM workload, does not grant canary/production authority, and does not merge into the operational branch.

## Main result

A fixed number of confirmation windows is not a robust universal default. Under equal all-null lifetime false-activation calibration, fixed-consecutive rules were substantially slower than accumulated-evidence rules in changing regimes.

The more important boundary is:

> dynamics-belief correctness != commit-authority optimality.

A HMM using the true transition hazard was strongest in some low/rare-change regimes, but CUSUM was stronger in medium/high-change regimes. Deliberately conservative authorization priors also performed well, but their numeric hazard values are synthetic-tuned and are not production defaults.

Fresh holdout examples (mean normalized control loss):

| Scenario | CUSUM | auth hazard .01 | dynamics-hazard comparator | Best |
|---|---:|---:|---:|---|
| symmetric .01 | 13.49 | 12.69 | 11.21 | dynamics comparator |
| symmetric .05 | 26.97 | 27.34 | 27.94 | CUSUM |
| symmetric .15 | 35.82 | 35.91 | 37.81 | CUSUM |
| rare .005/.05 | 5.08 | 5.29 | 4.26 | dynamics comparator |
| signal-persistent .08/.01 | 18.50 | 17.43 | 18.28 | conservative authorization prior |

No single method dominates every regime. CUSUM is retained as a simple shadow reference because it is nearly minimax in the tested panel and does not claim a transition hazard is known. Hazard-aware commit remains research-only pending real task-sequence calibration.

## Plugin disposition

The conversation-delivered incremental implementation adds a shadow-only commit detector with frozen calibration metadata and bounded scores:

- `fixed_consecutive`
- `cusum`

Outputs are limited to `SHADOW_KEEP_*` / `SHADOW_SWITCH_*`; `execution_authorized=false` always.

A maturity manifest separately tracks implementation status, value evidence and authority. Synthetic-only value evidence cannot become canary/production authority.

Local completed non-overlapping test chunks after this R3 change total 612 passing tests. A single all-tests invocation hit the execution time limit and is not claimed complete. The direct `shadow-commit` CLI smoke passed.

## Roadmap state

- R0: maturity guard implemented for the current subset; historical full-corpus normalization remains open.
- R1: real-model value and measured real cost remain externally blocked by the absence of a registered spend/model campaign.
- R2: prior local shadow/broker contracts remain tested.
- R3: synthetic/local comparison is closed; real-task calibration remains open.
- R4/R5: no canary/production authority.

## Reproduce

Python + NumPy, new output path:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python research/r3_commit_20260911/reproduce_r3_commit.py \
  --output /tmp/r3-commit.json
```

The script is synthetic only and emits `execution_authorized=false`.

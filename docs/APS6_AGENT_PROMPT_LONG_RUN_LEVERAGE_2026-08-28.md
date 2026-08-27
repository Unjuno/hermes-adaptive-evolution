# APS-6 — Agent Prompt Long-Run Trajectory Leverage — 2026-08-28

## H
Agent Prompt quality is a global control variable: because it affects action tendencies from every workflow state, improving it can move the stationary occupancy distribution of the whole organization rather than merely improve one local decision.

## T
- 7,000 heterogeneous finite organizations
- five workflow states
- exact stationary distributions under prompt variants
- prompt leverage scales 0.8, 1.6, 3.2
- 250,000-step trajectory validation at leverage 1.6.

## Stationary results

### Leverage 0.8

| Prompt | Welfare | Error occupancy | Gain vs raw | Gain/cost |
|---|---:|---:|---:|---:|
| raw | 0.821297 | 4.133% | +0.000000 | — |
| immutable_core | 0.832268 | 3.602% | +0.010971 | 0.019947 |
| core_plus_patch | 0.842657 | 3.133% | +0.021360 | 0.023733 |
| dense_prompt | 0.846618 | 2.947% | +0.025321 | 0.016336 |
| destructive_rewrite | 0.834465 | 3.368% | +0.013168 | 0.015492 |

### Leverage 1.6

| Prompt | Welfare | Error occupancy | Gain vs raw | Gain/cost |
|---|---:|---:|---:|---:|
| raw | 0.867666 | 2.145% | +0.000000 | — |
| immutable_core | 0.884030 | 1.603% | +0.016365 | 0.029754 |
| core_plus_patch | 0.898530 | 1.193% | +0.030864 | 0.034294 |
| dense_prompt | 0.903641 | 1.049% | +0.035975 | 0.023210 |
| destructive_rewrite | 0.885986 | 1.403% | +0.018320 | 0.021553 |

### Leverage 3.2

| Prompt | Welfare | Error occupancy | Gain vs raw | Gain/cost |
|---|---:|---:|---:|---:|
| raw | 0.929326 | 0.533% | +0.000000 | — |
| immutable_core | 0.946271 | 0.288% | +0.016945 | 0.030809 |
| core_plus_patch | 0.959164 | 0.154% | +0.029838 | 0.033153 |
| dense_prompt | 0.963124 | 0.118% | +0.033798 | 0.021805 |
| destructive_rewrite | 0.946872 | 0.221% | +0.017546 | 0.020642 |

At leverage 1.6:
- raw welfare: 0.867666
- core+patch welfare: 0.898530
- error occupancy: 2.14% -> 1.19%

Dense prompt achieved slightly higher raw welfare, but its larger modeled cost reduced its gain/cost relative to core+patch in the tested configuration.

Destructive rewrite had higher clarity than core+patch but lower fidelity; it consistently underperformed the provenance-preserving alternatives.

## Local prompt elasticity

| Leverage | Welfare gain per +0.01 clarity | dW/dclarity |
|---:|---:|---:|
| 0.8 | 0.000888 | 0.088772 |
| 1.6 | 0.001277 | 0.127723 |
| 3.2 | 0.001215 | 0.121536 |

## Long-trajectory validation, leverage 1.6

| Prompt | Exact stationary welfare | Empirical welfare | L1 occupancy error |
|---|---:|---:|---:|
| raw | 0.866414 | 0.866817 | 0.003003 |
| core_plus_patch | 0.897582 | 0.897795 | 0.001398 |
| destructive_rewrite | 0.884914 | 0.883900 | 0.006054 |

## D
- Prompt can be a global leverage point that changes long-run organization occupancy: PASS in this model.
- Prompt is universally the best bottleneck: not supported; leverage and cost determine the regime.
- provenance-preserving core+patch: positive evidence;
- destructive self-rewrite: negative evidence.

## C
Real LLM prompt elasticity may be much smaller, discontinuous, model-specific, or dominated by context-window cost.

## U
The unresolved empirical gate remains an independently sampled live/frozen LLM comparison with the same hard runtime.

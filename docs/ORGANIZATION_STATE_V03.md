# Organization State v0.3

`adaptive-evolution.organization-state.v0.3` is a **diagnostic vector state** derived from Hermes hook telemetry. It is not yet routing authority.

## Event-count notation

All topology quantities are dimensionless functions of event counts.

| Symbol | Meaning | Unit | Domain |
|---|---|---|---|
| `S_ij` | observed `subagent_start` count from parent `i` to child `j` | events | non-negative integer |
| `R_ij` | observed `subagent_stop` count for the same parent->child relation | events | non-negative integer |
| `C_ij` | conservatively completed relation count `min(S_ij, R_ij)` | events | non-negative integer |
| `q_ij` | share of source `i` traffic sent to `j` | 1 | `[0,1]` |

A missing stop is **not** imputed as a successful return.

## 1. Directed traffic breadth

For source `i` with outgoing traffic

```text
q_ij = S_ij / sum_j S_ij
H_i = -sum_j q_ij log(q_ij)
d_eff,i = exp(H_i)
b_i = d_eff,i / (N_active - 1)
```

The state reports the traffic-weighted average

```text
B = sum_i (sum_j S_ij) b_i / sum_ij S_ij
```

`B` is in `[0,1]`.

Interpretation:
- low `B`: each active source concentrates work into few children;
- high `B`: sources distribute work broadly.

It intentionally says nothing about global bottlenecks.

## 2. Interaction completion coverage

```text
C_ij = min(S_ij, R_ij)
coverage = sum_ij C_ij / sum_ij S_ij
```

The value is in `[0,1]` when any start exists, otherwise `None`.

This is **support metadata**, not a calibrated confidence probability. Equal coverage can correspond to very different topology error when a missing relation is a bridge rather than a redundant local edge.

## 3. Completed-flow connectivity

Use every node that appears in start evidence. Symmetrize only completed relations:

```text
A = C + C^T
L = I - D^(-1/2) A D^(-1/2)
G = lambda_2(L) / 2
```

where `lambda_2` is normalized-Laplacian algebraic connectivity. `G` is in `[0,1]`.

Semantics:
- no completed relation evidence at all -> `None` (unknown);
- some completed evidence but a start-observed node has no completed return path -> `0` (observed completed-flow graph is disconnected);
- otherwise larger values indicate fewer global bottlenecks in completed interaction relations.

The distinction between `None` and `0` is intentional: **unknown is not bad, and bad is not unknown**.

## 4. Role-conditioned traffic mixing

For Agent role posterior `p_i(r)` and confidence `c_i`, start traffic is weighted by role confidence:

```text
w_ij = S_ij c_i c_j
M = sum_ij w_ij [1 - dot(p_i, p_j)] / sum_ij w_ij
```

If no confidence-supported traffic exists, mixing is `None` rather than a prior-derived pseudo-measurement.

`role_conditioned_traffic_coverage` is reported separately.

## 5. Fragility

For tool/outcome evidence per Agent:

```text
fragility_i = (failures_i + 1) / (failures_i + successes_i + 2)
```

This is a Beta(1,1)-smoothed diagnostic rate, not a safety probability or causal vulnerability estimate.

## Deprecated diagnostic

`directed_diffusivity` is retained for backward-compatible experiment comparison only.

It uses a start-only row-stochastic operator and `1 - SLEM`. M2 falsification showed that delegation DAG sink/self-loop semantics can give misleading topology orderings. Its authority is explicitly:

```text
deprecated_diagnostic_only
```

Routers must not use it as an organization-control feature.

## Support and authority rule

No synthetic event-count cutoff authorizes production routing. State dimensions remain `diagnostic_only` until real Hermes task blocks demonstrate held-out **decision usefulness**.

If a state dimension is unavailable or unsupported, downstream code must fall back to the coarse/context-only decision path; it must never substitute numeric zero for missing evidence.

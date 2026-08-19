# Organization State v0.4

`adaptive-evolution.organization-state.v0.4` is a **diagnostic vector state** derived from Hermes hook telemetry. It is not yet routing authority.

The v0.4 change is semantic: completed-flow connectivity now uses a monotone algebraic-connectivity measure. The previous normalized-Laplacian definition could improve when a local return edge disappeared, so it was rejected for evidence semantics.

## Event-count notation

| Symbol | Meaning | Unit | Domain |
|---|---|---|---|
| `S_ij` | observed `subagent_start` count from parent `i` to child `j` | events | non-negative integer |
| `R_ij` | observed `subagent_stop` count for the same parent->child relation | events | non-negative integer |
| `C_ij` | conservatively completed relation count `min(S_ij, R_ij)` | events | non-negative integer |
| `q_ij` | share of source `i` traffic sent to `j` | 1 | `[0,1]` |

A missing stop is **not** imputed as a successful return.

## 1. Directed traffic breadth

For source `i` with outgoing traffic:

```text
q_ij = S_ij / sum_j S_ij
H_i = -sum_j q_ij log(q_ij)
d_eff,i = exp(H_i)
b_i = d_eff,i / (N_active - 1)
```

The state reports the traffic-weighted average:

```text
B = sum_i (sum_j S_ij) b_i / sum_ij S_ij
```

`B` is dimensionless and in `[0,1]`.

Interpretation:
- low `B`: active sources concentrate work into few children;
- high `B`: sources distribute work broadly.

It intentionally says nothing about global bottlenecks.

## 2. Interaction completion coverage

```text
C_ij = min(S_ij, R_ij)
coverage = sum_ij C_ij / sum_ij S_ij
```

The value is in `[0,1]` when any start exists, otherwise `None`.

**Coverage is support metadata, not confidence.** A falsification test held coverage fixed at 95.45% and found roughly an 8x difference in connectivity error depending on whether the missing return was a bridge or a redundant local relation.

## 3. Completed-flow connectivity

The node set is every Agent observed in start evidence. Completed relations are binarized and symmetrized:

```text
A_ij = 1 if C_ij + C_ji > 0 else 0
D_ii = sum_j A_ij
L = D - A
G = lambda_2(L) / N
```

where `lambda_2(L)` is the second-smallest eigenvalue of the **unnormalized** graph Laplacian. `G` is dimensionless and in `[0,1]`; a complete `N`-node graph maps to 1.

Why this definition:
- for a fixed node set, adding a non-negative edge Laplacian cannot decrease `lambda_2`;
- therefore adding completed-relation evidence cannot make connectivity look worse;
- conversely, removing return evidence cannot make connectivity spuriously better in the tested fixed-node setting.

Semantics:
- no completed relation evidence at all -> `None` (unknown);
- some completion evidence, but a start-observed Agent is isolated in the completed graph -> `0` (observed completed-flow graph is disconnected);
- otherwise larger values indicate fewer global bottlenecks.

The distinction between `None` and `0` is deliberate: **unknown is not bad, and bad is not unknown**.

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

`directed_diffusivity` remains only for backward-compatible experiment comparison.

It uses a start-only row-stochastic operator and `1 - SLEM`. Delegation-DAG falsification showed misleading topology orderings. Its authority is:

```text
deprecated_diagnostic_only
```

Routers must not use it.

## Evidence semantics

Three concepts remain separate:

1. **value** — e.g. `completed_flow_connectivity`;
2. **support** — e.g. `interaction_completion_coverage` and event counts;
3. **decision authority** — whether held-out real-task evidence shows that using the value improves routing.

No scalar support threshold inferred from synthetic experiments becomes a production gate. Missing or unsupported state must fall back to the coarser/context-only decision path; it must never be replaced by numeric zero.

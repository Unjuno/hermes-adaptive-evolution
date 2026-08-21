# Classification Resolution Trade-off Pilot — 2026-08-22

## Question
Does finer receiver classification always improve routing once storage, update cost, and concept drift are included?

## Design
- 48 agents, 4 information types, 260 steps, capability shift at step 130.
- 20 messages/step, 3 recipients/message; same bandwidth across policies.
- 120 paired seeds for the main comparison.
- Policies: random, fixed categorical role, receiver capability vector, sender-type x receiver x information interaction table.
- Utility per reception: +1 for useful transfer, -0.65 for harmful transfer.
- Cost-adjusted net utility subtracts normalized storage and model-update cost. Coefficients are pilot constants, not production defaults.

## Main results

| policy | raw utility | post-shift utility | harmful rate | normalized storage | normalized update | net utility |
|---|---:|---:|---:|---:|---:|---:|
| random | 0.324 | 0.325 | 0.410 | 0.000 | 0.000 | 0.324 |
| role | 0.416 | 0.259 | 0.354 | 0.0625 | 0.000 | 0.412 |
| capability | **0.478** | **0.390** | **0.317** | 0.250 | 0.500 | **0.443** |
| interaction | 0.455 | 0.375 | 0.330 | 1.000 | 1.000 | 0.355 |

The highest-resolution interaction representation did **not** win. Its extra degrees of freedom produced sparse estimation and higher memory/update cost. Capability-vector routing dominated this pilot.

## Memory half-life sweep
60 seeds/cell for capability and interaction models.

### Capability
| half-life | net utility | post-shift utility | harmful rate |
|---:|---:|---:|---:|
| 15 | **0.488** | **0.463** | **0.289** |
| 30 | 0.465 | 0.422 | 0.303 |
| 60 | 0.452 | 0.399 | 0.311 |
| 120 | 0.444 | 0.384 | 0.316 |

### Interaction
| half-life | net utility | post-shift utility | harmful rate |
|---:|---:|---:|---:|
| 15 | **0.406** | **0.455** | **0.300** |
| 30 | 0.380 | 0.412 | 0.315 |
| 60 | 0.362 | 0.381 | 0.326 |
| 120 | 0.353 | 0.366 | 0.332 |

Shorter memory won under this deliberately fast capability shift. This does not imply short memory is generally optimal; it establishes that representation resolution and memory time-scale interact.

## Decision

**PASS for the anti-overgeneralization hypothesis:** finer classification is not monotonically better. A middle-resolution capability representation produced the best cost-adjusted routing in this environment.

**FAIL for the naive high-resolution hypothesis:** interaction-specific state did not justify its storage/update cost and adapted more slowly because each cell received fewer observations.

## Next program-level consequence
The next experiments should not further tune this one toy environment. The program should branch to:
1. hierarchical memory promotion/demotion across information classes;
2. decentralized sender-side and receiver-side routing decisions;
3. equal-budget delayed abstraction vs immediate verbalization;
4. later, small-LLM confirmation of whichever mechanisms survive the toy screens.

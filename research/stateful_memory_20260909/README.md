# R1/R2: Stateful memory, episode evidence, and freshness — 2026-09-09

## Scope

Offline synthetic mechanism experiments plus a non-executing Shadow episode-evidence adapter. No provider call, live Hermes task, workflow dispatch, learned execution authorization, or operational-branch change was performed.

## Finding 1 — warm-start memory is part of the treatment

20 task types, 200 evaluation tasks, 2,000 replications:

- cold-start learner accuracy: 94.965%
- pre-endowed memory accuracy: 100%
- same algorithm with matched endowment: 100%

The apparent endowed-minus-cold advantage is 5.035 percentage points; endowed-minus-matched is zero. In the follow-up, the cold learner makes about 10.07 first-encounter errors, giving a break-even acquisition cost of about 0.503 error-equivalent utility per memory entry in this benchmark.

Conclusion: `policy code != policy state`. If acquisition is part of the evaluated lifecycle, charge it. If memory is an exogenous fixed asset, compare matched endowments instead.

## Finding 2 — task rows are not automatically independent evidence

Under an exact null, 40 independent episodes were generated with state-coupled tasks.

Primary counterexample, 10 tasks per episode with a common episode sign:

- treating 400 task rows as independent: 32.32% false positives;
- aggregating to 40 episode units: 3.98% false positives.

Fresh-seed ICC grid:

| Tasks/episode | ICC | Naive task FPR | Episode FPR |
|---:|---:|---:|---:|
| 2 | .50 | 9.26% | 5.30% |
| 5 | .50 | 18.40% | 5.60% |
| 10 | .50 | 25.04% | 6.22% |
| 20 | .90 | 34.62% | 5.56% |

The usual exchangeable-cluster design-effect approximation `1 + (m-1) rho` tracks why nominal task count can greatly exceed effective independent evidence count.

Conclusion: when policy memory couples tasks, define the evidence unit at the state-reset / causal-independence boundary. Episode aggregation does not itself prove episodes are independent.

## Finding 3 — task order is part of a stateful environment

A capacity-1 memory policy was evaluated on two task types whose long-run marginal distribution remains approximately 50/50 while Markov persistence changes.

| P(same next type) | Accuracy |
|---:|---:|
| .50 | 49.82% |
| .70 | 69.80% |
| .90 | 89.79% |
| .97 | 96.76% |
| .99 | 98.75% |

A deterministic same-multiset control produced 99% accuracy in block order and 0% in alternating order for the same capacity-1 policy.

Conclusion: `marginal task distribution != stateful evaluation environment`; the transition kernel / sequence is part of the intervention.

## Finding 4 — memory freshness is an FCV coordinate

A correct memory can be poisoned during a 300-step episode. Probe cost is 0.15 normalized utility per check.

At zero poison hazard, blind sticky memory is optimal because verification has cost and no benefit.

At poison hazard .002:

- sticky memory: mean net loss 72.509
- periodic every 10: 7.117
- failure-triggered verification with perfect sensitivity: 0.665

The verifier assumption was then weakened. With poison hazard .002 and no false alarms:

- verifier sensitivity .10: event-triggered loss 5.761 vs periodic-10 7.196;
- verifier sensitivity .05: event-triggered loss 10.502 vs periodic-10 7.143.

Conclusion: `memory value != memory freshness`, and event-triggered freshness dominates only when failure evidence is reliable enough relative to scheduled probe cost.

## R2 implementation disposition

The cumulative conversation patch adds `EpisodeProtocol` and `shadow-episode-evidence`.

The adapter freezes:

- candidate/baseline hashes;
- initial memory-state hashes;
- distinct mutable state namespaces;
- update-rule hashes;
- task sequence/order;
- evaluation mode (`matched_cold_start` or `policy_owned_endowment`);
- endowment cost treatment;
- score bounds and deadlines.

Behavior:

- `matched_cold_start` requires identical initial state contents but separate mutable namespaces;
- `policy_owned_endowment` allows different initial states and treats that endowment as part of the policy treatment;
- state transition receipts must form a chain in declared task order;
- inner task rows are never emitted as separate evidence units;
- missing tasks close conservatively with score bounds;
- evidence positivity never authorizes execution.

New episode-protocol tests: 14 passed. Finished non-overlapping compatibility chunks: 113 evidence/task/shadow-contract + 2 router + 95 shadow-ledger tests. A direct `shadow-episode-evidence` CLI smoke also passed. The full cumulative prior suite was attempted but some larger CLI/producer jobs exceeded the work-session execution window, so a complete all-suite pass is not claimed here.

## Reproduction

```bash
python research/stateful_memory_20260909/run_stateful_memory_study.py --output /tmp/stateful.json
python research/stateful_memory_20260909/followup_stateful_memory.py --output /tmp/stateful-followup.json
python research/stateful_memory_20260909/memory_verifier_frontier.py --output /tmp/memory-verifier.json
```

Tested locally with Python 3.13.5 and NumPy 2.3.5 on CPU. No throughput, token-cost, or provider-performance claim is made.

## Limits

These are mechanism counterexamples, not estimates of real Hermes memory correlation, poison frequency, or verifier sensitivity. Hashes do not authenticate actual memory contents, independence, update rules, or external services. Episode aggregation prevents a known task-level overcounting error but does not establish causal independence of episodes.

R1 remains synthetic validation. R2 remains non-executing Shadow infrastructure. The next practical gate is to define state-reset clusters and initial-memory ownership on real paired Hermes task sequences before using task outcomes as promotion evidence.

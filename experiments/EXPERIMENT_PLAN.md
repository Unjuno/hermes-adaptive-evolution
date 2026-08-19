# Experiment Plan

Experiments are ordered by **uncertainty that blocks the next design decision**, not by feature attractiveness.

## E1 — Real Hermes hook capture

**Priority:** P0

Hypothesis: public Hermes plugin hooks expose enough execution metadata to reconstruct useful parent/child and tool/outcome state without a fork.

Test:
- deterministic repository task;
- normal tool calls;
- one `delegate_task` child;
- deterministic failure and recovery;
- completion and one blocked/repeated-failure path where practical.

Measure:
- hook field presence/frequency;
- stable session/task/turn/subagent IDs;
- duplicate/missing/out-of-order rate;
- parent->child reconstruction;
- observer overhead.

Exit: replayable real-event corpus and compatibility matrix.

## E2 — Normalization and idempotent replay

Inject controlled corruption into an E1 corpus:
- duplicate 1/5/10%;
- drop 1/5/10%;
- bounded reordering;
- selected optional-ID removal.

Measure normalized identity/state equality, quarantined uncertainty, and attribution failures.

Exit: repeated replay is deterministic; malformed or incomplete evidence fails soft.

## E3 — Functional-role identifiability

Infer role from actual tool/action history. Compare lifetime counts, fixed windows, exponential forgetting, and adaptive/change-sensitive memory.

Measure accuracy, Brier/log-loss, calibration, role-change recovery latency, and false change rate.

Exit: choose role-memory behavior by held-out validation; no synthetic window constant becomes a production default.

## E4 — Directed interaction observability

Build the empirical directed operator from real interaction traffic and evaluate traffic-weighted role mixing, diffusivity/closure, and support indicators.

Primary metric is **decision usefulness**, not reconstruction of an imaginary hidden graph.

Exit: at least one topology proxy improves held-out routing or safely identifies when fine routing should not be used.

## E5 — Macro-state sufficiency / Markov falsification

Compare nested representations:

1. current coarse state;
2. + role-typed neighbor counts;
3. + lagged/message state;
4. + ordered/local identity;
5. + selected higher-order residual features.

Measure held-out log-loss/calibration, rare-failure recall, representation size, omitted-history residuals, and routing decision loss.

Exit: retain the smallest representation within practical resolution of the best validated decision performance.

## E6 — Finite-template router

Compare:
- best global organization;
- point task-context router;
- posterior-integrated task-context router;
- posterior + measured reconfiguration cost.

Use paired task seeds and stratified train/validation/final-test blocks.

Exit: better held-out net utility with no rare-event regression.

## E7 — Reconfiguration cost

Measure controlled changes in agent count, delegation template, role/prompt assignment, and later model/LoRA assignment.

Record wall time, tokens/compute, context loss/restart overhead, transient failure/recovery, and post-switch quality.

## E8 — Rare-event monitor

Evaluate coarse telemetry -> residual-triggered fine inspection on rare seed failures, cascades, and distribution-shifted motifs.

Use Average Precision, recall at fixed false-positive rate, escalation fraction, recovery latency, and damage containment.

## E9 — Controlled micro-probes

Only after E8 and only behind external safety controls. Compare passive warnings with low-risk controlled probes, including paired perturbations and nonlinear superposition residuals.

## E10 — Adaptive organization search

Only after E4-E9 are credible. Search safe coarse organization variables/templates before local graph mutations. Keep exploration budget for unsupported candidates and validate uncertain candidates with real paired benchmarks.

## E11+ — Skill, Teacher, LoRA

Skill evolution may proceed once real replay exists. Teacher and LoRA work requires verified trajectory provenance. Keep clean-success, recovery, correction/preference, and failure datasets distinct.

## Evaluation rules

- Evaluation tasks and active information-acquisition tasks are separate distributions unless explicitly declared otherwise.
- Paired comparisons share task/external randomness when possible.
- Unknown metrics are incomparable, not zero.
- Practical Pareto resolution must be explicit per metric.
- Synthetic sample complexity informs experiment design, not production activation authority.

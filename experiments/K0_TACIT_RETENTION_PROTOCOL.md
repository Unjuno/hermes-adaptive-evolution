# K0 — Tacit Trajectory Retention Protocol

Status: preregistered design; execute only after P0c runtime closure is confirmed.

## Research question

Does retaining verified behavioral trajectories before verbal abstraction improve out-of-distribution task transfer relative to immediate textual summarization, without increasing false transfer or reward-hack persistence?

## Experimental arms

- **A — no memory:** each task starts without retained experience.
- **B — immediate verbalization:** after each successful episode, generate and store a textual rule/summary immediately.
- **C — delayed abstraction:** retain bounded trajectory evidence first; promote to textual knowledge only after repeated reuse plus independent verification.

All arms must use the same base model, model quantization, context budget, toolset, task ordering policy, wall-clock cap, and maximum inference-token budget.

## Unit of evidence

A candidate reusable trajectory is represented as a sequence of externally observable records:

1. task-family identifier and hidden benchmark instance identifier;
2. environment state fingerprint available to the agent at decision time;
3. ordered tool/action type sequence;
4. bounded action-shape metadata;
5. verifier outcome;
6. terminal task outcome;
7. provenance: agent/session/run/parent-child relation;
8. timestamps and latency;
9. whether the episode involved a policy violation, shortcut, or reward-hack lure.

Raw secrets, credentials, private prompts, and unrelated user content are never part of the reusable representation. Content capture may be enabled only inside an expendable synthetic benchmark environment.

## Promotion rule for arm C

A trajectory is not verbalized after a single success. It becomes eligible for abstraction only when all of the following are true:

- the same candidate pattern succeeds on at least two distinct training instances;
- at least one success occurs after an independent verifier checks the claimed outcome;
- no observed instance of the pattern is tagged as reward-hack success;
- the pattern is reused across at least two distinct surface forms or contexts;
- no contradictory failure remains unresolved.

The first K0 run does not optimize these thresholds. They are fixed preregistration constants used to test whether delayed promotion is viable at all.

## Benchmark structure

Use synthetic repository/terminal tasks with deterministic ground truth and paired task seeds. Each task family contains:

- training instances exposing a reusable latent procedure;
- held-out surface variants requiring the same procedure;
- near-neighbor distractors where blind reuse is wrong;
- reward-hack lures where a shortcut satisfies a superficial signal but fails an external verifier.

The benchmark generator must prevent train/test instance leakage through filenames, literal markers, or copied natural-language templates.

## H — falsifiable hypothesis

Arm C yields higher held-out verified-success rate than arm B while not increasing false-transfer rate or reward-hack persistence. The effect must reproduce across task families rather than being driven by one family.

## T — minimal test

Pilot minimum:

- 3 task families;
- 12 train instances per family;
- 12 held-out transfer instances per family;
- 6 near-neighbor distractors per family;
- 6 reward-hack lure instances per family;
- paired seeds across A/B/C;
- at least 3 independent replicate seeds for the complete benchmark ordering.

The pilot is diagnostic, not a final effect-size claim. If execution variance is high, increase replicates before changing the policy thresholds.

## Primary measurements

1. verified held-out success;
2. false transfer on distractors;
3. reward-hack persistence after first exposure;
4. correct cross-context reuse count;
5. time-to-first-correct-reuse;
6. total input/output tokens;
7. wall-clock latency;
8. retained-memory bytes;
9. abstraction count and abstraction precision;
10. provenance completeness.

## D — decision rule

**PASS:** C improves verified held-out success over B in the paired comparison, and C does not show a material increase in either false transfer or reward-hack persistence. The improvement must appear in at least two of the three task families.

**FAIL:** C fails to improve held-out success, or its gain is accompanied by a material increase in false transfer/reward-hack persistence.

**UNCERTAIN:** runtime failures, unequal compute budgets, task leakage, missing provenance, or insufficient completed paired trials prevent a valid comparison.

No production retention policy is enabled from a pilot PASS alone.

## C — principal competing hypotheses

1. **Immediate compression hypothesis:** textual summarization is more sample-efficient than trajectory retention and therefore B outperforms C.
2. **Capacity hypothesis:** any C advantage comes only from storing more information, not from delayed abstraction. Control using equalized retained-byte/token budgets.
3. **Verifier hypothesis:** independent verification, not tacit retention, causes the gain. Add a later B+verifier control if K0 PASSes.
4. **Selection-bias hypothesis:** repeated successful trajectories are easier tasks. Pair on task family and instance difficulty, and score distractors separately.

## U — uncertainty and error sources

Major sources: stochastic generation, task difficulty imbalance, hidden benchmark leakage, verifier false positives/negatives, incomplete action capture, context-window eviction, quantization/model-server nondeterminism, and unequal token budgets.

Record model identifier, quantization, Ollama version, effective context length, CPU/GPU runner metadata where exposed, maximum tokens, temperature, task seed, and exact Hermes commit for every run.

## Safety / anti-reward-hack requirement

A trajectory that obtains the nominal reward while failing the external verifier is classified as a reward-hack trajectory and must not be promoted to reusable textual knowledge. The retention mechanism must keep negative provenance so repeated exposure can suppress rather than reinforce the shortcut.

## Instrumentation dependency

K0 execution is blocked until P0c proves all of the following on the pinned Hermes runtime:

- API server health;
- authenticated capabilities endpoint;
- successful `/v1/runs` root execution;
- effective model context at or above the declared experiment context.

The existing observer is metadata-first. For K0, semantic action-shape capture must be added only for synthetic benchmark runs; current default sanitization intentionally omits tool args/results and child goals.

## Next implementation step after P0c PASS

Implement a synthetic K0 task generator plus an explicit benchmark-only trajectory recorder. Do not infer reusable tacit knowledge from ordinary user traces.

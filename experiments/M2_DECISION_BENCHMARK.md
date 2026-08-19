# M2 Decision Benchmark — Does Organization State Improve Routing?

The M2 estimator is useful only if its observables improve a downstream organization decision. This benchmark therefore evaluates **decision loss**, not topology reconstruction error.

## Question

Does adding observed organization state improve held-out organization selection over a task-context-only router?

The first comparison is:

```text
Router A: task context only
Router B: task context + observed topology/support state
```

Do not compare against an oracle hidden graph in the primary metric.

## Initial safe template library

Start with four bounded templates. They are deliberately coarse; arbitrary graph mutation belongs to M5.

1. `solo`
   - root agent only;
   - no delegation.
2. `one_leaf`
   - root -> one leaf;
   - serial completion.
3. `two_leaf_serial`
   - root -> leaf A -> return -> root -> leaf B;
   - two completed root/child relations.
4. `implement_then_review`
   - implementation leaf followed by a distinct verification/review leaf;
   - reviewer may recommend a correction but does not receive broader permissions.

## Task regimes

Use deterministic repository fixtures with hidden final checks. Initial regimes:

1. `single_local_fix`
   - narrow defect, low decomposition value.
2. `diagnose_then_fix`
   - diagnosis and implementation can be separated.
3. `verification_critical`
   - plausible wrong fixes are easy; independent review is valuable.
4. `two_independent_subproblems`
   - two changes can be reasoned about independently, then integrated.

Each regime must contain multiple distinct fixtures. Do not let a regime equal one benchmark instance.

## Paired evaluation

For each task instance, every candidate template receives the same:

- repository snapshot;
- model/checkpoint/adapter;
- task text;
- random seed where provider supports it;
- external time/resource limits;
- final hidden verifier.

This is common-random-numbers / paired experimental design. Organization is the treatment.

## Outcome vector

Keep dimensions separate before any utility collapse:

- `verified_success` — binary;
- `quality` — task-specific normalized verifier score where applicable;
- `recovery_success` — whether an encountered failure was detected and recovered;
- `terminal_failure` — binary;
- `unsafe_or_scope_violation` — binary;
- `wall_seconds`;
- `model_tokens_or_provider_usage` when observable;
- `delegation_count`;
- `reconfiguration_cost` when switching from a previous organization.

Rare/safety regressions are hard constraints, not small negative utility terms.

## Observed M2 state

Router B may use only values available from the observer:

- task/context features available to Router A;
- `directed_traffic_breadth`;
- `completed_flow_connectivity`;
- `interaction_completion_coverage`;
- confidence-gated role mixing;
- role-conditioned traffic coverage;
- fragility/outcome support;
- identity uncertainty/support diagnostics.

The legacy `directed_diffusivity` is forbidden as routing authority.

## Support gating

Do not invent a synthetic event-count threshold. A state dimension can be:

- `unavailable`;
- `diagnostic_only`;
- `eligible_for_validation` after real data supports it.

If support is insufficient, Router B must fall back to Router A for that dimension.

## Splits

Use three disjoint blocks:

1. discovery/train;
2. router/model selection;
3. final test.

Split by **task fixture/family**, not by repeated runs of the same fixture, to avoid trajectory leakage.

## Primary metrics

1. held-out routing regret relative to the best candidate among the declared finite template library;
2. verified success rate;
3. terminal/unsafe failure rate;
4. net wall-clock/compute cost;
5. frequency of unsupported fine-state use (must be zero).

Secondary:

- calibration of predicted template advantage;
- switching/chattering rate in sequential tasks;
- complementarity, e.g. `P(template B succeeds | template A fails)`.

## Decision rule for M2 exit

M2 is supported only if, on an independent final-test block:

- context + observed state reduces routing regret or safely abstains more effectively than context-only;
- no rare/safety regression is introduced;
- improvement persists across multiple task regimes;
- unsupported state never becomes an implicit zero/default feature;
- results are not driven by one template or one fixture family.

A lower topology-prediction MSE without lower decision loss does **not** pass M2.

## Execution tiers

### CI/offline

Use fake/deterministic provider responses only to validate:

- template plumbing;
- paired snapshot reset;
- metric collection;
- observer replay;
- split isolation.

Do not use CI CPU model timings as evidence for RTX/local deployment performance.

### Provider canary

Run a very small number of real local-model tasks to confirm each template is executable and observable.

### Local GPU benchmark

The real template comparison should run on the target local GPU environment so latency, concurrency and memory tradeoffs are representative.

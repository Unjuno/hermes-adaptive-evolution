# R1/R2: reviewed paired-task producer and cross-arm isolation — 2026-09-08

## Scope

This study connects actual local subprocess outcomes to the prior TaskProtocol in the cumulative downloadable implementation patch. It executes three small hand-authored Python repair fixtures (clamp, unique, total) with finite reviewed scripts. This is NOT a live Hermes/LLM benchmark, NOT autonomous repair synthesis, and NOT an arbitrary-code sandbox. No provider call, workflow dispatch, operational branch merge or learned execution authorization was performed.

This branch contains a standalone runnable reproducer and this report. The full task-protocol bridge, cumulative prior R2 files, tests, plans, detailed receipts and reports are delivered in the conversation package, not implied to be merged into the operational plugin. The standalone reproducer uses smaller assertions than the integrated producer and reproduced the same failure directions. Its fetched Git blob SHA was checked against the executed local source: `3d96458105040b90f0e02cc5ce9f1034e1b6ccfe`.

## Endpoint fixed before execution

Success requires a pristine initial task snapshot, unchanged protected tests, normal worker exit within the registered worker timeout, and successful completion of a separately staged fixed verifier. Candidate stdout is not success evidence. Known timeout/crash is score zero for this endpoint. Known verifier unavailability or worker launch failure is unknown, not zero. Evaluating only a surviving repaired artifact is a different valid endpoint that must be declared separately, not substituted after observing a run.

Every candidate and baseline attempt starts in a separate temporary workspace. Four fixed attempts per fixture are completed regardless of early success. Repeated executions remain attempts within one registered fixture-family unit, not new independent evidence. The three chosen families do not support population-level performance inference.

## Primary execution study

Each row comprises 12 candidate executions (3 fixture families x 4 attempts), paired with a noop baseline started from a separate pristine snapshot.

| Candidate | Local test exit zero | External functional verification passed | Declared endpoint success |
|---|---:|---:|---:|
| Correct fixed repair | 12/12 | 12/12 | 12/12 |
| Rewrite only local tests | 12/12 | 0/12 | 0/12 |
| Self-report success only | 0/12 | 0/12 | 0/12 |
| Repair then timeout | 12/12 | 12/12 | 0/12 |
| Repair then abnormal exit | 12/12 | 12/12 | 0/12 |

Noop baseline succeeded in zero trials. These counts validate deliberately constructed operational controls; they do not estimate model quality or real-world failure prevalence.

## Follow-up 1: exit code zero is not proof of completed verification

A reviewed candidate places `raise SystemExit(0)` in the solution. In 12/12 trials the local test and external verifier processes exit zero, but no completed assertion receipt exists. Requiring a valid completion receipt rejects all 12 as successes.

The receipt checks cover schema, count, boolean outcomes and consistency in the integrated producer. They do not authenticate evidence from hostile same-UID code; such code could attempt forgery. Never run arbitrary generated programs on this backend.

## Follow-up 2: sharing the worktree changes the comparison

| Workspace | Execution order | Mean raw candidate-minus-baseline score | Pairs |
|---|---|---:|---:|
| Separate pristine copies | baseline then candidate | 1.0 | 12 |
| Separate pristine copies | candidate then baseline | 1.0 | 12 |
| Shared, no reset | baseline then candidate | 1.0 | 12 |
| Shared, no reset | candidate then baseline | 0.0 | 12 |

When the candidate repairs first, the noop baseline receives repaired code. Balancing the order yields a shared-workspace average of 0.5, not the pristine comparison of 1.0. Random order alone therefore does not remove this carryover. This is a deterministic counterexample, not a new statistical theorem.

The strict producer refuses a non-pristine input before starting the second policy. The deliberately relaxed research path records INPUT_CONTAMINATION with score unknown rather than promoting it as valid paired evidence.

## Implementation and tests

The delivered bridge records protocol, candidate, baseline, metric and snapshot hashes; declared attempt schedules; monotonic local receipts; policy exit and timeout; protected-file integrity; local diagnostic results; and independent verifier results. It journals attempts and emits the prior task-protocol event schema, then verifies full deterministic replay and duplicate-event idempotency. No EVIDENCE_POSITIVE claim is drawn from this three-family fixture study. Learned execution authority remains false.

Implementation tree: 275 tests passed in one run (227 prior + 48 added). A fresh known-upstream subset was patched and all 275 tests passed again in one command. Fresh application, upgrade from the prior task-protocol package, unchanged reapplication, all 38 payload hashes, and unknown-edit refusal were checked. This is not the whole upstream/Hermes test suite. Direct Git checkout in the execution environment failed because github.com DNS was unavailable; repository research publishing used the connected GitHub tool.

## Startup negative result retained

The first smoke used -I -B under a 0.4-second worker limit. All six reviewed worker attempts timed out during environment startup. A mechanism probe showed system site initialization overhead; the standard-library-only reviewed backend was changed to -I -S -B. The failed smoke is retained in the package. Single startup measurements are not presented as a comparative performance benchmark. Changing startup flags is not a security boundary.

## Reproduce the operational counterexamples from this branch

Python 3.11+ on POSIX, standard library only. CPU clock is not pinned. This is not a throughput or LLM benchmark.

```bash
python research/paired_producer_20260908/reproduce_isolation.py --repeats 4 --output /tmp/paired-producer-reproduction.json
```

The command refuses an existing output file and runs only built-in reviewed fixtures. It creates temporary workspaces, not provider tasks.

After applying the separate cumulative package, the full bridge can be invoked explicitly:

```bash
python -m adaptive_evolution_observer.paired_fixture_producer --run-reviewed-fixtures --candidate fix --attempts 4 --output /tmp/paired-fixture-run
python -m adaptive_evolution_observer.paired_fixture_producer --audit --output /tmp/paired-fixture-run
```

## Trust boundary and next gate

Same-user subprocesses, fresh directories and process groups are operational controls, not containment against adversarial code. Network, external services, caches and model memories are not isolated. Hashes establish local consistency, not authentic preregistration or causal independence. The next practical gate requires a genuine isolated Hermes paired-task producer with independently controlled scoring and measured budgets. The current backend must not be exposed as a model-facing arbitrary execution tool.

Primary implementation references: Python subprocess documentation for start_new_session, explicit timeout cleanup and child environment; Python command-line documentation for -I/-S. The claims above are based on the recorded local fixture executions, not on documentation alone.

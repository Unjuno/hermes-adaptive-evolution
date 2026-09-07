# R1/R2: task aggregation, censoring and completion order — 2026-09-08

## Scope

This is an offline synthetic follow-up to r1-weak-cluster. No provider calls, paid probes, workflow dispatch, execution authorization, or production-branch changes were performed. The numerical tests use independently generated worlds, 3000 replications per condition, 500 registered tasks per replication. Methods share generated tasks for paired comparison. Alpha=.05 and betting fractions [0,.02,.05,.1,.2,.4,.8] were fixed before running.

The initial question was whether unique task IDs were sufficient for the evidence contract. They are not: within-task aggregation, missingness and the order presented to the test also matter. These are applications/counterexamples to existing conditional-mean inference, not claims of new universal statistical theory.

## Finding 1 — outcome-dependent retry changes the estimand

Under a symmetric +/-1 fixed-budget task-effect null, stop after a positive first attempt; otherwise take the second attempt and average the observed attempts.

- Fixed two-attempt mean: 46/3000 crossings = 1.53%; mean -0.001027.
- Stopped observed-count mean: 3000/3000 = 100%; mean +0.248789.
- Exact enumeration gives stopped mean expectation +0.25 versus fixed-budget expectation 0.

Task IDs remain unique and tasks remain independent. The stopped mean is a different, upward-biased input relative to the original fixed-budget estimand. This is NOT a counterexample to an e-process theorem: its conditional-null input requirement was violated.

Fresh-seed paired binary-score follow-up, with both candidate and baseline success probability .60:

- Fixed two-attempt mean: 41/3000 = 1.37%.
- Stop after candidate wins on first attempt: 2848/3000 = 94.93%.
- Exact expected stopped difference .12; empirical .120096.

A genuinely deployed retry policy may be a valid different policy to evaluate, provided its endpoint and costs are declared in advance. Do not conflate that policy with single-run/fixed-budget policy evaluation.

## Finding 2 — dropping missing effects or filling with zero does not repair selection

Original mean zero. Positive effects are missing with probability .10; negative effects with probability .50.

| Analysis | Crossings |
|---|---:|
| Full outcomes reference | 59/3000 = 1.97% |
| Complete cases only | 2992/3000 = 99.73% |
| Missing effect replaced by zero | 2992/3000 = 99.73% |
| Include all tasks using a known-range lower bound | 4/3000 = 0.13% |

For the fixed-fraction process with minimum gain zero, a zero contribution multiplies capital by one. It can therefore be equivalent to deleting the row. Missing values cannot be assumed to be zero.

The lower-bound method does not require missingness independent of the effect. It requires correctly prespecified score bounds and the original task-effect conditional-null contract. It is conservative, not a recovery of unobserved truth.

### Negative result: missingness bounds can lose substantial power

At true mean .20:

- Lower bounds without additional observation: 720/3000 = 24.00%.
- Prespecified random audit of half the initially missing results: 2033/3000 = 67.77%.
- Complete-outcome reference: 2874/3000 = 95.80%.

At mean .06, lower bounds detect only 21/3000 versus 391/3000 with complete outcomes. Extra observation has possible value, but real audit cost was not measured. The audit simulation resolves results before final task evidence construction; it does not reopen already consumed evidence after seeing the test result.

## Finding 3 — completion order alone can break sequential validity

Fresh-seed follow-up: all 500 tasks eventually return; none is dropped. Negative results have a three-unit additional simulated completion delay.

| Order | Any crossing | Terminal positive |
|---|---:|---:|
| Prespecified enrollment order | 62/3000 = 2.07% | 3/3000 |
| Completion-time order | 3000/3000 = 100% | 3/3000 |

Terminal decisions agree in every world because the fixed-bet terminal product is permutation invariant. Running maxima are not invariant. Early arrivals are outcome-selected. Buffering and feeding the closed enrollment-order prefix preserves the intended ordering, provided enrollment itself was outcome-independent and the original conditional-null contract holds.

## Local implementation

A cumulative downloadable patch adds `shadow-task-evidence` ahead of the prior low-level `shadow-evidence` interface:

- Freeze candidate/baseline/metric, task registry, attempt budget, score bounds and deadlines into a protocol hash.
- Aggregate paired scores using the fixed denominator; missing candidate/baseline scores become intervals.
- Consume only lower bounds, in closed enrollment-order prefix order.
- Buffer future completed tasks; account for fully missing registered tasks at deadline.
- Identical attempt replay is idempotent; conflicting data and changed protocol are rejected.
- Late results are accounted but cannot overwrite closed evidence.
- A positive evidence result never authorizes execution.

227 local tests passed across three groups (164 previous +63 new). New/fresh application, previous-bundle upgrade, idempotent reapplication, unknown-edit refusal, and hashes of all 27 applied payload files were checked. A post-apply CLI concurrency test also passed. Combined post-apply full-test commands exceeded the execution time budget and are NOT claimed completed. This is not the entire upstream suite or a live Hermes deployment.

The new runtime module and full patch are delivered as a conversation artifact, not merged into an operational branch by this research commit. The low-level manual task-effect API still assumes correctly constructed input; this new adapter does not authenticate external data.

## Remaining limitations

Hashes cannot prove preregistration, real task independence, causal validity, honest receipt clocks or a lifetime error budget. Unknown effects must be bounded honestly. Fixed enrollment order alone is not enough when tasks are selected by outcomes or when only an unconditional grand-average null holds. Float64 overflow checks are implemented, but no rigorous interval-arithmetic guarantee at a threshold is claimed.

R1 remains synthetic validation. R2 remains non-executing replay. The next practical gate is a real paired-task producer emitting policy hashes, bounded scores, retry indexes and trustworthy timestamps into this contract, not adding more unrestricted self-evolution mechanisms.

## Reproduction

Tested: Python 3.13.5, NumPy 2.3.5, SQLite 3.46.1, Linux, Intel Xeon Platinum 8573C, BLAS threads=1. CPU clock not pinned; no throughput/LLM benchmark.

```bash
mkdir -p research/results
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/task_protocol_20260908/run_protocol_study.py --output research/results/protocol_study.json
OPENBLAS_NUM_THREADS=1 python research/task_protocol_20260908/followup_protocol_study.py
```

The scripts emit per-method counts, Wilson intervals, per-world arrays and source hashes. Complete initial/follow-up plans and proof derivations are in the delivered artifact; source hashes are recorded in the result files. Local preregistration is not an external timestamp service.

## Primary sources

- Waudby-Smith & Ramdas, Estimating means of bounded random variables by betting. DOI:10.1093/jrsssb/qkad009; arXiv:2010.09686.
- Shin, Ramdas & Rinaldo, On the Bias, Risk, and Consistency of Sample Means in Multi-armed Bandits. DOI:10.1137/20M1361249; arXiv:1902.00746.

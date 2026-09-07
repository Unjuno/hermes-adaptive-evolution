# R1 weak effects, evidence units and family budgets — 2026-09-08

## Scope and status

This branch records a new autonomous, bounded work session. It does not enable execution, alter production settings, change existing workflow definitions, or dispatch a workflow. Existing operational branches are unchanged.

The previous statement that all recent BAC/R1/R2 theory and implementation had already been synchronized to GitHub was too broad: the active research index still pointed to BAC-20. The current new experiment sources are committed here. Historical BAC-21 onward and the complete latest R2 implementation archive are NOT implied to be integrated by this branch.

Evidence kind: synthetic mechanism experiments plus local shadow-contract tests. No new live Hermes task, paid provider call, or real probe-cost measurement was performed.

## Finding 1: two separately significant batches are not a generally efficient default

The previous strong-signal comparison did not include a pooled fixed-horizon test with the same total evidence. We added that comparator, then performed a fresh-seed follow-up matching both evidence count and nominal null error.

Learned-policy experiment: 800 randomized discovery probes, 700 independent evaluation probes, 20,000 evaluation-only task points; frozen baseline/candidate and sensor-group estimator; 160 replications per amplitude.

| Nonlinear amplitude | Two separate 5% tests both pass | Pooled 5% test | Two-look final regret | Pooled final regret |
|---:|---:|---:|---:|---:|
| 0.000 | 1/160 | 4/160 | 0.0008295 | 0.0008302 |
| 0.002 | 0/160 | 6/160 | 0.0010173 | 0.0010161 |
| 0.006 | 2/160 | 34/160 | 0.0022388 | 0.0020330 |
| 0.012 | 30/160 | 115/160 | 0.0045549 | 0.0028988 |
| 0.040 | 160/160 | 160/160 | 0.0041659 | 0.0041659 |

Equal data does not mean equal false-positive risk: under a fixed independent common null, two 5% tests both passing have nominal 0.25% probability. Accordingly the fresh-seed Gaussian follow-up compares both procedures at nominal 0.25%, with 700 total observations and 10,000 repetitions per row.

| Standardized mean | Two halves, each 5% | Pooled, 0.25% |
|---:|---:|---:|
| 0.00 | 25/10000 | 27/10000 |
| 0.02 | 95/10000 | 115/10000 |
| 0.04 | 359/10000 | 440/10000 |
| 0.08 | 1885/10000 | 2436/10000 |
| 0.15 | 7734/10000 | 8833/10000 |

Conclusion: withdraw two-independent-z>1.645 as a general preferred default. Independent evidence is essential; requiring every batch to be independently significant is a different and sometimes costly requirement. Replication across substantively different environments remains a separate objective.

Important endpoint correction: zero nonlinear generating amplitude is a structural null, not necessarily nonpositive incremental value of two fitted policies. Learned-policy promotion rates are NOT automatically calibrated type-I error rates. Exact policy-gain nulls are tested separately below.

## Finding 2: anytime-valid inference has a power tradeoff

A simple prespecified finite betting mixture is tested on bounded task differences in {-1,0,+1}, disagreement mass 0.30. Maximum 1000 independent tasks, 3000 replications per mean. The mixture fractions are [0,.02,.05,.1,.2,.4,.8].

| True mean | Pooled fixed 5% | Repeated uncorrected 5% | Anytime betting |
|---:|---:|---:|---:|
| 0.00 | 4.53% | 20.90% | 2.00% |
| 0.01 | 14.90% | 37.00% | 4.10% |
| 0.03 | 54.57% | 73.23% | 21.47% |
| 0.06 | 96.93% | 98.33% | 78.37% |
| 0.12 | 100.00% | 100.00% | 100.00% |

At mean 0.12, anytime stopping consumed median 160.5 tasks; at mean 0.03, it often exhausted all 1000 tasks. These are simulated evidence units, not measured LLM latency or money. The offline simulator generates complete trajectories for comparison; this is not proof of actual provider-call savings.

## Finding 3: replay is not independent evidence

Under the exact null, 200 independent task differences were copied eight times each. 3000 replications:

- Correct 200-unit betting: 34/3000 false crossings = 1.13%.
- Treating 1600 copied rows as fresh evidence: 1719/3000 = 57.30%.
- Fixed z-test falsely treating copied rows as independent: 904/3000 = 30.13%.

This violates the conditional-null assumption; it is not a counterexample to the martingale theorem. Changing invocation IDs or seeds does not prove independence.

## Finding 4: anytime validity per candidate is not family-wide validity

20 prespecified candidates, each 200 independent task units, 2000 null families:

- Unadjusted 5% budget for every candidate: 386/2000 families with at least one false crossing = 19.30%.
- Total family budget 5%, divided across candidates: 10/2000 = 0.50%.

The empirical 0.50% is not the guarantee. Under the conditional-mean and registration assumptions, a union-bound allocation limits this frozen family's risk to 5%. No claim is made for untracked creation of fresh families or candidates selected using evaluation evidence.

## Implementation disposition

A new shadow-only `shadow-evidence` replay module was implemented and packaged locally with the prior R2 layer. It checks frozen candidate/baseline hashes, metric identity, prespecified bounds, task-unit idempotency, family alpha allocations, and evidence horizon. A positive result is `EVIDENCE_POSITIVE`, never execution authorization. Same-unit same-data replay contributes zero new evidence; conflicting data is rejected.

The delivered subset passed 164 tests, including the prior 117. This is NOT the full upstream/Hermes test suite and NOT a live runtime deployment. The full R2 archive has not been merged into this branch. Runtime promotion remains pending.

Checksums and IDs cannot establish causal validity, real independence, honest preregistration, or a system-lifetime error budget. Gaussian/IPW outcomes in the weak-signal experiment are not silently clipped and fed to the bounded theorem.

## Reproduce

Tested: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Linux, CPU, BLAS thread count 1. No GPU/LLM benchmark.

From repository root, with NumPy/SciPy already available:

```bash
mkdir -p research/results
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/r1_20260908/run_experiments.py --stage weak --output research/results/weak.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/r1_20260908/run_experiments.py --stage bounded --output research/results/bounded.json
OPENBLAS_NUM_THREADS=1 python research/r1_20260908/followup.py
```

The two stages emit per-method rates, Wilson intervals, learned-policy seed records, paired regret contrasts and environment metadata. The follow-up writes `research/results/followup.json`. Runtime timings are incidental local measurements, not comparative speed claims.

## Statistical foundation, not claimed novelty

- Waudby-Smith and Ramdas, Estimating means of bounded random variables by betting. DOI 10.1093/jrsssb/qkad009; arXiv:2010.09686.
- Howard et al., Time-uniform, nonparametric, nonasymptotic confidence sequences. DOI 10.1214/20-AOS1991; arXiv:1810.08240.

The simple mixture here is a conservative implementation of the general method, not a reproduction of every optimized method from these papers.

## Next gate

Validate independently defined real task clusters and bounded causal metrics before adding any execution authority. Prefer the simplest fixed-horizon evaluation when sequential stopping adds no measured net value. R1 production status remains unresolved; R2 remains non-executing shadow infrastructure.

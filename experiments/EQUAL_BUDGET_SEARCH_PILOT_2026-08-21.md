# Equal-Budget Search Pilot — 2026-08-21

Status: diagnostic toy-model result; not an LLM result.

## Question

Does contradiction-triggered candidate generation outperform constant random exploration when the candidate-generation budget is equalized?

## Design

- 600 seeds per condition;
- 120 steps, environment shift at step 30;
- continuous candidate space [0,1];
- initial candidate pool clustered around the pre-shift optimum 0.25;
- post-shift optimum 0.75;
- common observations can favor stale/shortcut knowledge;
- rare observations are more diagnostic;
- exactly 12 candidate births per trial in every condition.

Compared:

1. constant: births are spread across the post-shift horizon;
2. triggered: births occur after accumulated contradiction;
3. hybrid: contradiction trigger plus sparse periodic births.

## Results

| policy | success rate | first-good mean | first-good median | final best distance | births |
|---|---:|---:|---:|---:|---:|
| constant | 0.2900 | 81.75 | 90 | 0.2202 | 12 |
| triggered | 0.2383 | 82.62 | 90 | 0.2092 | 12 |
| hybrid | 0.2633 | 83.12 | 90 | 0.2152 | 12 |

Success means that a candidate within 0.10 of the current optimum attained score > 0.45 before the 90-step post-shift horizon expired.

## Interpretation

The earlier apparent advantage of contradiction-triggered generation did **not** survive this equal-budget control. Constant exploration found a usable post-shift candidate more often (29.0%) than triggered exploration (23.8%) in this regime. Triggered exploration did end with a slightly smaller mean best-candidate distance, but the effect did not translate into higher success probability.

Therefore the program-level conclusion is:

> Contradiction-triggered search is not an unconditional improvement. Its apparent benefit can come from spending more/earlier search effort after failures. Search policies must be compared under equal candidate-generation budgets and explicit time-to-discovery metrics.

This is a useful negative result. It prevents the project from hard-coding “failure -> generate more candidates” as if it were already established.

## H/T/D/C/U

**H:** At equal candidate-generation budget, contradiction-triggered exploration finds a valid alternative faster or more often than constant exploration.

**T:** 600 paired seeds per policy, 12 births per trial, same environment and scoring process.

**D:** PASS if triggered has higher success rate and no worse time-to-first-good; FAIL if it is worse on success or materially slower; UNCERTAIN if differences are negligible relative to stochastic error.

**Decision:** FAIL for the simple triggered policy in this toy regime.

**C:** Constant exploration can outperform because it searches before contradiction evidence becomes strong, avoiding trigger latency and local-parent lock-in.

**U:** The generator mutates top-scoring candidates rather than learning a proposal distribution; the environment has one abrupt shift; no semantic structure exists. Follow-ups should test trigger rules that combine contradiction with diversity/uncertainty and should measure candidate novelty explicitly.

## Next design consequence

Do not optimize exploration trigger in isolation. The next cross-lane priority is verifier-domain/quorum structure and phase-control cost, followed by tacit-vs-explicit retention under equal information budgets.

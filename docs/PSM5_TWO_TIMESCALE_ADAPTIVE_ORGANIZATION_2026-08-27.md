# PSM-5 — Two-Timescale Adaptive Organization — 2026-08-27

## H
A stochastic organization should not necessarily update its transition structure at the same cadence as its internal workflow transitions. There may be an intermediate update cadence that is slower than internal mixing but faster than environmental drift.

## T
- episodes: 5,000
- steps/episode: 1800
- primitive support mix: 0.02
- reward noise SD: 0.22
- switching cost: 0.025
- compared fixed structure and update periods 1, 5, 20, 80, 240 steps.

## Results

| Policy | Mean welfare | Dynamic regret/step | Updates | Mixing proxy |
|---|---:|---:|---:|---:|
| fixed | 0.662210 | 0.337790 | 0 | — |
| same_timescale_u1 | 0.863106 | 0.136894 | 1800 | 1.504 |
| u5 | 0.872128 | 0.127872 | 360 | 1.479 |
| u20 | 0.823388 | 0.176612 | 90 | 1.540 |
| u80 | 0.744594 | 0.255406 | 22 | 1.550 |
| u240 | 0.698520 | 0.301480 | 7 | 1.530 |

## D
The best retained cadence was **u5**, welfare **0.872128**.

Internal mixing-time proxy was about 1.5 steps for adaptive policies. Updating every 5 steps outperformed both same-step adaptation and slower 20/80/240-step updates in this construction.

Interpretation:
- "slow" is not sufficient;
- the useful condition is **internal mixing faster than structural adaptation, while structural adaptation remains faster than material environment drift**;
- excessive structural delay cannot track the regime;
- same-step updating is more sensitive to noisy single-transition evidence.

This is synthetic evidence, not a general proof of the optimal ratio.

## C
A different reward-noise level or drift timescale may move the optimal update period. The correct design target is therefore a timescale ratio, not a fixed number such as 5.

## U
Next needed quantity: online estimate of effective mixing time and drift time, so the plugin can choose its own structural-update cadence.

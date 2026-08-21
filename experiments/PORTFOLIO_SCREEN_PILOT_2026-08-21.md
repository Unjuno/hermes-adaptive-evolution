# Portfolio Screen Pilot — 2026-08-21

Status: diagnostic toy-model screen; not an LLM result.

## Design

A 2^5 factorial diagnostic screen was run over 32 cells with 50 paired seeds per cell.

Factors:

- propagation: low / high;
- verifier failure domains: 1 / 8;
- memory: fixed / evidence-adaptive half-life;
- exploration: constant / contradiction-triggered;
- phase policy: fixed periodic verification / adaptive verification trigger.

Environment:

- 24 agents;
- 160 steps;
- optimum shifts at step 80;
- continuous candidate knowledge in [0,1];
- a superficially attractive shortcut region near 0.5;
- common-context reward plus rare/counterfactual verification;
- temporally correlated verifier-domain failures.

The purpose is to detect interactions and bad assumptions, not to optimize final constants.

## Marginal descriptive results

| Factor | Level | final good | final hack | hack takeover | verification phases |
|---|---|---:|---:|---:|---:|
| propagation | low | 0.1423 | 0.3588 | 0.2112 | 59.47 |
| propagation | high | 0.0880 | 0.4053 | 0.5325 | 55.78 |
| memory | fixed | 0.1178 | 0.3968 | 0.3912 | 57.60 |
| memory | adaptive | 0.1125 | 0.3673 | 0.3525 | 57.65 |
| exploration | constant | 0.0674 | 0.3535 | 0.3375 | 67.06 |
| exploration | triggered | 0.1629 | 0.4106 | 0.4062 | 48.19 |
| phase | fixed | 0.1107 | 0.3939 | 0.4050 | 40.00 |
| phase | adaptive | 0.1197 | 0.3702 | 0.3388 | 75.25 |

The 1-vs-8 verifier-domain marginal was essentially neutral in this implementation because each verification event sampled only one domain; there was no quorum/consensus mechanism. This is an experimental-design limitation, not evidence that verifier independence is useless.

## Best observed cell by final-good-first ranking

- propagation: low;
- verify domains: 1;
- memory: fixed;
- exploration: contradiction-triggered;
- phase: fixed;
- final good mean: 0.2784;
- final hack mean: 0.3205;
- hack takeover rate: 0.08;
- adaptation delay median: full 80-step post-shift horizon (criterion not reached);
- verification phases: 40.

## Interpretation

1. **High propagation was consistently dangerous in this regime.** It more than doubled hack-takeover risk in the marginal comparison (0.5325 vs 0.2112) while reducing final-good prevalence.

2. **Contradiction-triggered exploration increased discovery but also increased shortcut exposure.** It raised final-good prevalence substantially, but also increased final-hack and takeover risk. Therefore the next experiment must equalize candidate-generation budget and measure search efficiency rather than treating triggered exploration as an unconditional win.

3. **Adaptive phase control reduced hack metrics but spent much more verification budget.** The present trigger is not yet efficient: roughly 75 verification phases on average versus 40 for the fixed controller. The next phase-control test must include explicit verification cost and must tune/control trigger frequency.

4. **Evidence-adaptive memory modestly reduced hack prevalence/takeover but did not improve final-good prevalence in this factorial regime.** This indicates strong interactions with search and propagation and argues against optimizing memory in isolation.

5. **Absolute performance remained poor.** Even the best cell did not reach the predeclared sustained adaptation criterion after the environment shift. Therefore this screen is a mechanism-discovery diagnostic, not a successful end-to-end architecture.

## Program decisions

- STOP treating any single mechanism (half-life, candidate generation, curator, phase switching) as the research program.
- PRIORITIZE the following cross-cutting tests:
  1. equal-budget contradiction-triggered vs constant exploration;
  2. explicit quorum-based independent verifier domains with correlated failure;
  3. adaptive phase control under a verification-cost constraint;
  4. partial/context-dependent knowledge and negative transfer;
  5. tacit-to-explicit abstraction under equal retained-information budgets;
  6. role/organization emergence from behavior rather than predefined labels.

## H/T/D/C/U for this pilot

**H:** System-level outcomes depend on interactions among propagation, verification, forgetting, exploration, and phase control; optimizing one factor in isolation will mislead design.

**T:** 32-cell factorial diagnostic screen, 50 seeds/cell, paired pseudo-random seeds by cell.

**D:** PASS if at least one factor changes sign or usefulness depending on another factor, or if marginally attractive mechanisms fail end-to-end criteria. The pilot supports this: triggered exploration improves discovery while worsening hack exposure; adaptive phase control improves hack metrics while sharply increasing verification cost.

**C:** A single dominant mechanism might explain most performance and make the factorial program unnecessary. This was not observed.

**U:** Toy dynamics, low absolute performance, descriptive marginals without formal factorial ANOVA, and a verifier-domain implementation that lacks quorum. Follow-up experiments must correct these limitations.

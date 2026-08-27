# Probabilistic Organization Progress — 2026-08-28 v3

New Agent Prompt track:
- APS-1: prompt is a global lever but not automatically the dominant bottleneck; downstream marginal allocation outperformed prompt-only and transition-only baselines.
- APS-2: repeated destructive prompt self-rewrite increased clarity while degrading source fidelity and creating semantic failures; immutable versioned patches retained fidelity in the synthetic model.
- APS-3: prompt leverage has a measurable break-even regime; in the retained sweep, prompt was the best initial intervention for a majority only from leverage scale 2.8 upward.
- APS-4: prompt evolution and organizational transition evolution should be separate control coordinates; dual-axis adaptive allocation was best across all tested leverage regimes.
- APS-5: immutable prompt-core assembly rejected all tested reserved-core override attacks with zero normal false rejects; naive last-writer-wins assembly allowed core override in 28.74% of all mixed cases.
- `HUMIES_AGENT_PROMPT_CORE_V0_1.md` created as an experimental control-plane prompt contract. It explicitly remains outside the hard safety TCB.

Retained architecture:
hard runtime kernel -> probabilistic organization -> evidence boundary -> slow transition learning, plus an orthogonal immutable-core/versioned-patch Agent Prompt control surface selected by bottleneck-adaptive marginal value.

Next:
1. independent live/frozen LLM A/B test of the agent prompt core;
2. mutating semantic sleeper attack against Intent/Effect Locator;
3. online prompt-vs-transition bottleneck attribution under real workload telemetry.

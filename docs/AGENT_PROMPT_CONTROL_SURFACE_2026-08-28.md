# Agent Prompt as an Independent Global Control Surface — 2026-08-28

## Scope

This experiment track treats the Humies agent prompt as a **separate global control surface** from the probabilistic organizational transition kernel. The prompt can influence behavior in every workflow state, while the transition kernel controls where the organization moves. Hard safety remains outside both.

All performance numbers below are synthetic mechanism experiments unless stated otherwise. The prompt contract itself is a design artifact and has not yet been validated with an independently sampled live/frozen LLM runner.

## Architecture under test

```text
immutable agent-prompt core + versioned prompt patches
        |                         |
        | global behavior prior   | prompt evolution
        v                         v
finite stochastic organization / transition kernel P_t
        |
        v
proposal / action
        |
        v
hard runtime boundary
```

The prompt axis and transition-kernel axis are optimized separately by downstream marginal value/cost.

## APS-1 — Global prompt leverage vs local organization intervention

Systems: 6,000; budget steps: 8.

Initial mean prompt gain/cost: **0.007473**.
Initial best local transition gain/cost: **0.011178**.
Prompt was the best first intervention in **18.17%** of systems.

| Strategy | Final welfare | Gain | Mean prompt updates | Mean transition updates |
|---|---:|---:|---:|---:|
| prompt_only | 0.846131 | 0.034084 | 8.00 | 0.00 |
| org_only | 0.891390 | 0.079343 | 0.00 | 8.00 |
| prompt_first_3 | 0.883682 | 0.071635 | 3.00 | 5.00 |
| local_error | 0.816337 | 0.004289 | 0.00 | 8.00 |
| adaptive_marginal | 0.893208 | 0.081160 | 1.09 | 6.91 |

Decision: **Prompt is a real global lever, but global scope alone does not make it the current bottleneck.** The adaptive marginal allocator achieved the best mean welfare (0.893208). Among systems that first used prompt and later moved to organization intervention, mean migration occurred around step 3.93.

## APS-2 — Destructive prompt self-rewrite vs immutable provenance

Episodes: 12,000; steps: 500.

| Policy | Success | Final clarity | Final fidelity | Mean updates | Semantic failure |
|---|---:|---:|---:|---:|---:|
| none | 81.864% | 0.600 | 1.000 | 0.00 | 0.000% |
| one_time | 83.868% | 0.672 | 1.000 | 1.00 | 0.000% |
| destructive_any_failure | 84.177% | 0.985 | 0.532 | 79.12 | 7.685% |
| gated_destructive | 86.485% | 0.942 | 0.855 | 19.56 | 2.938% |
| gated_immutable | 88.725% | 0.946 | 1.000 | 20.34 | 0.000% |
| immutable_any_failure | 90.019% | 0.985 | 1.000 | 49.90 | 0.000% |
| batched_immutable | 85.485% | 0.823 | 1.000 | 8.09 | 0.000% |

Key negative result: destructive rewrite on every failure pushed clarity to 0.985, but fidelity collapsed to 0.532 and semantic failures rose to 7.68%. Immutable versioned patches preserved source fidelity in this model.

This supports a prompt supply-chain invariant:

> Improve prompt behavior through immutable-source, versioned patches/annotations; do not repeatedly replace the current prompt with its own rewritten descendant.

## APS-3 — Prompt leverage break-even

Prompt global leverage was swept from 0.2 to 6.0 while local transition interventions were held fixed.

| Prompt leverage scale | Prompt/best-local gain ratio | Prompt is best fraction |
|---:|---:|---:|
| 0.2 | 0.136 | 0.00% |
| 0.5 | 0.313 | 0.09% |
| 1.0 | 0.554 | 8.61% |
| 1.7 | 0.822 | 30.81% |
| 2.2 | 0.984 | 43.74% |
| 2.8 | 1.159 | 54.64% |
| 3.5 | 1.345 | 63.60% |
| 4.5 | 1.585 | 73.37% |
| 6.0 | 1.906 | 83.19% |

The first tested scale where prompt improvement was best for a majority of systems was **2.8**.

Decision: there is a measurable **prompt-leverage regime**. The correct policy is not `prompt first` or `transition first`, but to estimate the global prompt leverage and compare its downstream marginal value/cost to competing control surfaces.

## APS-4 — Separate prompt and transition axes

Budget: 8.0; systems per leverage regime: 5,000.

| Prompt leverage | Best policy | Final welfare | Prompt updates | Transition updates |
|---:|---|---:|---:|---:|
| 0.7 | dual_axis_adaptive | 0.878829 | 0.43 | 7.12 |
| 1.3 | dual_axis_adaptive | 0.910630 | 1.08 | 6.54 |
| 2.8 | dual_axis_adaptive | 0.959215 | 2.41 | 5.42 |
| 4.5 | dual_axis_adaptive | 0.983178 | 3.61 | 4.39 |

The **dual-axis adaptive** policy was best at every tested leverage level. It automatically allocated more updates to prompt as prompt leverage increased, without forcing prompt and organizational transition updates to happen together.

Decision: **prompt evolution and self-transition evolution should be distinct control coordinates.** Coupling every change wastes budget because the two axes are not generally co-bottlenecks at the same time.

## APS-5 — Prompt supply-chain integrity

A concrete immutable Humies agent-prompt core was created. Dynamic prompt material is accepted only through typed slots; reserved core clauses cannot be overwritten.

Cases: 60,000; attack probability: 36%.

- naive last-writer-wins core override rate: **28.74%**
- strict core override rate: **0.00%**
- strict attack reject rate: **100.00%**
- strict normal false reject rate: **0.00%**

Attack families: authority override, retry-bypass override, core rewrite, learning-credit rebinding, and unknown patch kinds.

This tests supply-chain integrity only; it does **not** prove that the prompt improves a live LLM.

## Proposed Humies control state

The evolving controller should keep these separate:

```text
X_t = (workflow_state, hidden_context_belief, transition_kernel_version,
       prompt_core_version, prompt_patch_set, evidence_state)
```

The fast stochastic workflow evolves mainly through the transition kernel. The prompt is an orthogonal global behavior prior whose version changes on a slower, evidence-gated path.

## H / T / D / C / U

### H
Agent prompt quality is a global leverage variable that should be optimized independently from organizational self-transition. Its interventions should be selected by downstream marginal value/cost, and prompt evolution should preserve immutable source intent/provenance.

### T
APS-1 through APS-5 above, including 6,000–12,000-system/episode synthetic experiments, leverage sweeps, dual-axis budget allocation, and 60,000 prompt-patch integrity cases.

### D
- Prompt is a meaningful global control surface: **PASS in synthetic model**.
- Prompt is always the first bottleneck: **FAIL**.
- Destructive repeated self-rewrite: **FAIL**.
- Immutable/versioned prompt evolution: **provisional PASS**.
- Separate prompt and transition control coordinates: **positive evidence**.
- Strict prompt-core assembly: **PASS for structural integrity in the tested assembler**.
- Actual live-LLM prompt-quality improvement: **UNCERTAIN / not yet tested independently**.

### C
A sufficiently strong base model may make prompt intervention marginal, or a real LLM may react nonlinearly to modular prompt patches. Long prompt cores may also introduce context cost that is absent from the current synthetic model.

### U
The major unresolved quantity is the **real LLM downstream elasticity to agent-prompt changes**, including interaction with context length, model family, tool use, and long-horizon behavior.

## Next empirical gate

Use the immutable prompt core as an experimental treatment in the existing frozen/live LLM proposer gate:

1. baseline agent prompt;
2. immutable core only;
3. core + task-specific patch;
4. core + Impact Locator + sparse specialist annotations;
5. destructive sequential rewrite ablation.

Measure downstream task success, semantic drift, malformed proposals, hard-boundary rejections, retry churn, token cost, and error correlation. Keep hard runtime identical across all conditions.

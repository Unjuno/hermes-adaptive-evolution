# Research Status — 2026-08-28

Active branch: `experiment/p0-runtime-closure`.

## Start here

1. [`docs/BAC_TRACK_PROGRESS_2026-08-28_V18.md`](docs/BAC_TRACK_PROGRESS_2026-08-28_V18.md) — causal bottleneck allocator / model / representation evolution through BAC-20.
2. [`docs/BAC19_BAC20_LATENT_SYNTHESIS_REPRESENTATION_LIFECYCLE_2026-08-28.md`](docs/BAC19_BAC20_LATENT_SYNTHESIS_REPRESENTATION_LIFECYCLE_2026-08-28.md) — latent synthesis, compression, merge, and retirement gate.
3. [`docs/BAC17_BAC18_REPRESENTATION_BIRTH_EVIDENCE_BOUNDARY_2026-08-28.md`](docs/BAC17_BAC18_REPRESENTATION_BIRTH_EVIDENCE_BOUNDARY_2026-08-28.md) — representation-birth evidence boundary / telemetry poisoning.
4. [`docs/EXPERIMENT_PROGRESS_2026-08-28_V18.md`](docs/EXPERIMENT_PROGRESS_2026-08-28_V18.md) — latest compact experiment progress.
5. [`docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md`](docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md) — Agent Prompt global control surface.
6. [`docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md`](docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md) — immutable experimental prompt core.
7. [`docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md`](docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md) — finite workflow / hidden context stochastic control.
8. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — earlier retained hard-runtime architecture.

## Current system thesis

Build a Humies-oriented adaptive organization/control plugin in which Agent Prompt, organization transition policy, semantic Locator, Verifier allocation, model population, and state representation can evolve independently according to downstream causal value, while a minimal external trusted runtime hard-blocks unsafe execution transitions.

Current learned state is conceptually:

```text
workflow
+ Prompt state/version
+ hidden-context belief
+ organization state/kernel
+ semantic Locator/Verifier state
+ pending causal-effect state
+ credit-kernel version
+ future-interaction model
+ dynamics-model identity/lifecycle
+ representation version/group/lifecycle
+ causal-support/exploration state
```

The hard-runtime boundary remains external to all learned quantities.

## Retained findings

### Hard runtime
- Parsing != Authorization; Typing != Authority; Integrity != Freshness; Validation != Commit.
- Hard invariants are lexicographically prior to performance optimization.
- Learned Prompt, belief, transition model, Locator, model identity, and representation are not authorization authority.

### Prompt + probabilistic organization
- Prompt is an orthogonal global behavior control surface, not the workflow transition kernel.
- Prompt globality does not imply Prompt is always the bottleneck.
- Immutable prompt core + versioned patches is preferred to destructive self-rewrite.
- Finite workflow + hidden context can be modeled as a controlled stochastic process; pending causal effects may need explicit state augmentation.

### Causal bottleneck allocation
- NO-OP is a first-class action.
- Hidden confounding requires causal support.
- Immediate marginal value is insufficient under persistence, delayed outcomes, mediation, and future control interactions.
- Credit horizon, persistence horizon, and planning horizon are distinct.

### Model and representation evolution
- Model diversity != Model freshness and != Model coverage.
- Unseen regimes require model birth; model birth requires reversibility and retirement.
- Parameter adaptation != Representation adaptation.
- Residual search != Structural evidence; independent heldout validation is required.
- Telemetry novelty != Representation-birth authority; committed-effect evidence remains the promotion boundary.
- BAC-19: representation birth can synthesize a compact latent coordinate rather than only select a supplied feature. Eight-seed replication: latent synthesis beat direct primitive expansion `8/8`, with `0/8` stationary false births.
- BAC-19c: the compact latent beat direct primitive expansion at every tested sample size and reduced deployment action-model coefficients from `168` to `60`.
- BAC-20: Representation merge != provenance deletion. Destructive merge failed after one constituent changed semantics; provenance-preserving logical merge allowed independent retirement.
- BAC-20b: degraded constituent retirement `20/20`, stable false retirement `0/20`.

## Compact numerical result

- [`results/bac19_bac20_summary_2026-08-28.json`](results/bac19_bac20_summary_2026-08-28.json)

Detailed BAC-19/20 reproduction scripts remain in the working experiment archive and are not claimed as committed in this GitHub update.

## Current next gates

1. BAC-21 primitive-map insufficiency / sensor birth: no function of current primitives can recover the missing state.
2. Observation acquisition competing with Prompt / Organization / Locator / Verifier by Future Control Value.
3. Correlated poisoning of representation-promotion evidence.
4. Joint model-birth + representation-birth controller.
5. Independent frozen/live LLM/Humies behavior gate while preserving the frozen external hard runtime.

## Evidence status

All BAC/APS/PSM numerical findings remain synthetic mechanism evidence unless explicitly labeled live. Independent real Humies/LLM downstream elasticity and end-to-end production failure semantics remain unresolved.
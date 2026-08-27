# Research Status — 2026-08-28

Active branch: `experiment/p0-runtime-closure`.

## Start here

1. [`docs/BAC_TRACK_PROGRESS_2026-08-28_V17.md`](docs/BAC_TRACK_PROGRESS_2026-08-28_V17.md) — causal bottleneck allocator / model / representation evolution through BAC-18.
2. [`docs/EXPERIMENT_PROGRESS_2026-08-28_V17.md`](docs/EXPERIMENT_PROGRESS_2026-08-28_V17.md) — latest compact experiment progress.
3. [`docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md`](docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md) — Agent Prompt global control surface.
4. [`docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md`](docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md) — immutable experimental prompt core.
5. [`docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md`](docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md) — finite workflow / hidden context stochastic control.
6. [`docs/PSM5_TWO_TIMESCALE_ADAPTIVE_ORGANIZATION_2026-08-27.md`](docs/PSM5_TWO_TIMESCALE_ADAPTIVE_ORGANIZATION_2026-08-27.md) — two-timescale organization update.
7. [`docs/PSM6_TELEMETRY_POISONING_RESISTANCE_2026-08-27.md`](docs/PSM6_TELEMETRY_POISONING_RESISTANCE_2026-08-27.md) — telemetry poisoning / committed-effect boundary.
8. [`docs/PSM7_SLEEPER_POISONING_VERIFIER_INDEPENDENCE_2026-08-27.md`](docs/PSM7_SLEEPER_POISONING_VERIFIER_INDEPENDENCE_2026-08-27.md) — verifier independence.
9. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — earlier retained hard-runtime architecture.

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
+ representation version
+ causal-support/exploration state
```

The hard-runtime boundary remains external to all learned quantities:

```text
strict/canonical proposal decode
-> authoritative security binding
-> freshness/replay prevention
-> semantic prospective invariant
-> commit binding / anti-TOCTOU
-> certified fallback
-> local hold
-> independent capability suspension
```

## Retained high-level findings

### Hard runtime
- Parsing != Authorization; Typing != Authority; Integrity != Freshness; Validation != Commit.
- Hard invariants are lexicographically prior to performance optimization.
- Learned Prompt, belief, transition model, Locator, model identity, and representation are not authorization authority.

### Prompt + probabilistic organization
- Prompt is an orthogonal global behavior control surface, not the workflow transition kernel.
- Prompt globality does not imply Prompt is always the bottleneck.
- Immutable prompt core + versioned patches is preferred to destructive self-rewrite.
- Finite workflow + hidden context can be modeled as a controlled stochastic process; weak recovery support is preferable to high randomization.
- Structural organization updates require a slower timescale than operational workflow mixing.

### Causal bottleneck allocation
- NO-OP is a first-class action.
- Hidden confounding requires causal support; weak global randomized support + modest targeting outperformed pure targeting in the tested family.
- Immediate marginal value is insufficient under persistence, delayed outcomes, mediation, and future control interactions.
- Credit horizon, persistence horizon, and planning horizon are distinct.
- Pending causal effects may need to be represented in state to restore useful Markov structure.

### Model and representation evolution
- Model diversity != Model freshness and != Model coverage.
- Unseen regimes require model birth; model birth requires reversibility and retirement.
- Parameter adaptation != Representation adaptation.
- Residual search != Structural evidence: in-sample representation search false-birthed in 20/20 stationary runs at candidate pools 16/64/256; heldout validation false-birthed 0/20 in the same stress.
- Telemetry novelty != Representation-birth authority: poisoned telemetry caused 12/12 false births, while independent authoritative committed-effect validation caused 0/12 in BAC-18.

## Reproduction/result entry added in this update

- `results/bac17_bac18_summary_2026-08-28.json`

The detailed BAC-17/18 local scripts are intentionally not claimed as archived by this commit; this update first restores the GitHub source-of-truth/ledger and compact result state.

## Current next gates

1. BAC-19 latent-feature synthesis: construct new latent state features rather than selecting a supplied correct candidate.
2. BAC-20 representation lifecycle: merge/retire redundant born features.
3. Correlated poisoning of telemetry and pseudo-verifier evidence for false model/representation birth.
4. Joint model-birth + representation-birth controller.
5. Independent frozen/live LLM/Humies behavior gate while preserving the frozen external hard runtime.

## Evidence status

All BAC/APS/PSM numerical findings remain synthetic mechanism evidence unless explicitly labeled live. Independent real Humies/LLM downstream elasticity and end-to-end production failure semantics remain unresolved.

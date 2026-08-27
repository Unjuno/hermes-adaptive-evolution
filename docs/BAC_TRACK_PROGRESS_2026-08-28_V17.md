# Bottleneck Allocator / Causal Evolution Track — 2026-08-28 v17

This document is the compact source-of-truth for the BAC experiment line. All conclusions below are synthetic unless explicitly stated otherwise. Hard safety remains external to statistical optimization.

## Research objective

Build a Humies-oriented adaptive controller that chooses among Prompt, Organization, Locator, Verifier, exploration, model/representation updates, and NO-OP by downstream causal value while preserving a minimal trusted runtime boundary.

## Retained progression

### BAC-1 to BAC-3 — bottleneck allocation and NO-OP
- Local error frequency is not a causal bottleneck measure; recovery-aware downstream value is required.
- Logged contextual counterfactual models can recover intervention value in the synthetic benchmark.
- `NO-OP` is a first-class action. Forced self-improvement is invalid after marginal value becomes non-positive.
- Exploration is itself a control variable; fixed exploration forever is wasteful after convergence.

### BAC-4 to BAC-6 — hidden confounding and causal support
- Strong unobserved confounding collapses observational Direct/IPW allocation.
- Randomized micro-interventions provide a causal anchor but are sample-hungry.
- Pure targeted exploration failed under replication because it removed support elsewhere.
- Retained structure: weak global causal-support floor + modest contextual targeting.
- Causal positivity is the learning analogue of weak primitive recovery support.

### BAC-7 to BAC-10 — future control value and delayed credit
- Immediate marginal gain is not full control value when interventions persist or change later intervention value.
- Short 2–3 step Future Control Value (FCV) planning captured most finite-horizon value in the tested family.
- Prompt-first is not universal; Prompt can be complementary or substitutive with later controls.
- Immediate reward attribution can reverse Prompt/Verifier ranking when Prompt effects are delayed.
- Credit horizon, persistence horizon, and planning horizon are distinct.
- Prompt-conditioned delayed-credit models plus short FCV planning outperformed stale/immediate credit models.

### BAC-11 to BAC-12 — mediation and pending causal state
- Prompt can change whether later Organization/Locator/Verifier controls are invoked at all.
- `Post-treatment adjustment != Total control value`: freezing a downstream mediator removes part of Prompt's organizational leverage.
- With overlapping delayed effects, current workflow/quality state is not Markov-sufficient.
- Action history alone is not necessarily a sufficient statistic for unrealized effects.
- Explicit pending causal-effect state strongly reduced allocator regret in the synthetic mechanism.

### BAC-13 to BAC-14 — hidden-state filtering and model freshness
- Hidden pending-credit state can be inferred from action/state/outcome streams, but better latent-state RMSE does not guarantee lower decision regret.
- Hidden organizational context and pending causal residue are complementary belief-state components.
- `Model diversity != Model freshness`: a model bank can accumulate enough old evidence to lock into a stale model.
- A switching/change hazard produced replicated improvement after joint transition/credit-kernel drift.

### BAC-15 to BAC-16 — unseen model birth and lifecycle
- `Model diversity != Model coverage`: a new regime outside the bank requires an UNKNOWN/novelty path.
- Over-conservative model-birth thresholds miss real drift.
- Model birth without reversibility creates lock-in when an old regime returns.
- Retained lifecycle: KNOWN -> UNKNOWN/NOVELTY -> PROVISIONAL BIRTH -> COMMITTED MODEL -> SWITCH/DECOMMISSION -> RETIRED.
- New models need provisional commitment while old models retain weak support.

### BAC-17 — representation birth
- Structural drift was introduced that no coefficient refit inside the old Prompt/Organization/Locator/Verifier feature space could express.
- Single-seed: old-space refit regret `0.006869`; representation birth `0.000021`; oracle representation `0.000018`.
- 12-seed replication: representation birth 12/12; correct structural-family first pick 12/12; stationary false birth 0/12.
- Mean accuracy: old-space refit `48.43%`; representation birth `92.38%`.
- New principle: `Parameter adaptation != Representation adaptation`.

### BAC-17c — representation-search multiple testing
- Candidate pools 16, 64, 256 were tested.
- Naive in-sample scanner: stationary false representation birth 20/20 at every pool size.
- Independent heldout gate: stationary false birth 0/20 at every pool size while retaining 20/20 detection under structural drift.
- New principle: `Residual search != Structural evidence`.

### BAC-18 — telemetry poisoning and false representation birth
- Stationary world; old representation is sufficient.
- Untrusted telemetry was poisoned to make an irrelevant feature appear structurally useful.
- Telemetry-authorized representation birth: 12/12 false births; attack decoy selected 12/12.
- Independent authoritative committed-effect holdout: 0/12 false births.
- Clean deployment accuracy fell `91.37% -> 66.21%`; regret rose `0.000117 -> 0.001877` after false representation birth.
- New principle: `Telemetry novelty != Representation-birth authority`.

## Current evolution coordinates

The adaptive system now has at least three distinct evolution layers:

1. **Parameter evolution** — Prompt patches, routing, organization transition parameters, verifier budget.
2. **Model-population evolution** — model birth, switching, specialization, retirement.
3. **Representation evolution** — state variables / feature maps / latent coordinates themselves.

Conceptually:

`(phi_t, M_t, Theta_t) -> (phi_(t+1), M_(t+1), Theta_(t+1))`

where representation promotion follows:

`discovery residual -> candidate -> independent heldout validation -> authoritative committed-effect validation -> provisional representation -> downstream policy-value validation -> commit`.

## Current augmented control state

```text
workflow state
+ Prompt state/version
+ hidden-context belief
+ organization transition state
+ Locator/Verifier state
+ pending causal-effect state
+ credit-kernel version
+ future-interaction model
+ active dynamics-model identity/lifecycle
+ representation version
+ causal-support/exploration state
```

Hard runtime authority, freshness, commit binding, fallback, replay protection, and capability suspension remain outside this learned state.

## Invalidated / superseded findings retained

- BAC-3 forced-intervention design was invalidated; NO-OP was added.
- BAC-6 single-seed targeted-exploration positive result reversed under replication.
- BAC-7a early two-step implementation under-counted persistence and was superseded.
- BAC-9 `high uncertainty -> depth 1` heuristic failed; high uncertainty truncated deep rollout to depth 2 instead.
- BAC-12 action-history augmentation was insufficient; explicit pending state superseded it.
- BAC-13 first policy comparison confounded filter quality with planner-horizon error.
- BAC-15 initial novelty threshold was too conservative and failed to trigger.
- BAC-16 initial retirement rule did not fire and was superseded by holdout testing.

## Next gates

1. **BAC-19 latent-feature synthesis** — construct a new latent representation rather than selecting an already supplied correct candidate.
2. **BAC-20 representation lifecycle** — merge/retire redundant born features and measure representation debt.
3. **Representation-birth security** — correlated telemetry + pseudo-verifier poisoning; committed-effect/verifier-independence boundary.
4. **Joint model + representation birth** — a new representation should be able to spawn a new dynamics-model family.
5. **Live Humies/LLM gate** — replace synthetic proposer/behavior components without moving hard safety into the model.

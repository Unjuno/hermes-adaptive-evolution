# Research Status — 2026-08-27

The active research branch is `experiment/p0-runtime-closure`.

Start here:

1. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — retained hard-runtime architecture and findings through v15;
2. [`docs/EXPERIMENT_LEDGER_CURRENT.md`](docs/EXPERIMENT_LEDGER_CURRENT.md) — decision ledger through the v15 runtime gate;
3. [`docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md`](docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md) — latest completed serialized parser gate;
4. [`docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md`](docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md) — finite workflow / infinite ergodic trajectory and hidden-context organizational control;
5. [`docs/ONLINE_TRANSITION_ADAPTATION_2026-08-27.md`](docs/ONLINE_TRANSITION_ADAPTATION_2026-08-27.md) — online transition-model adaptation under context drift;
6. [`docs/NEXT_ACTIONS.md`](docs/NEXT_ACTIONS.md) — frozen/live LLM proposer gate for the hard-runtime track.

## Hard-runtime track

The serialized parser gate remains conditionally passed. The retained runtime boundary is:

```text
bounded serialized proposal
  -> object/array-distinguishing strict parse
  -> duplicate/unknown field policy
  -> exact schema + tool identity
  -> exact decimal/fixed-precision checks
  -> explicit canonicalization only
  -> authoritative security binding
  -> token freshness / replay prevention
  -> commit binding / anti-TOCTOU
  -> certified fallback
  -> local hold
  -> independent capability suspension
```

Important retained invariants:

- parsing is not authorization;
- typing is not authority;
- integrity is not freshness;
- validation is not commit;
- canonical syntax is not automatically canonical remote semantics;
- statistical optimization does not replace hard invariants.

The next empirical hard-runtime gate still replaces only the synthetic proposer with an independently sampled frozen/live LLM over mock tools. The model remains outside parsing, authority, freshness, commit, fallback, and suspension.

## Probabilistic organization / Humies plugin track

A parallel organization-control track now models the Prompt Supply Chain and agent placement as a finite stochastic workflow rather than a hand-written procedural loop.

Current retained model:

```text
finite workflow states
  + persistent hidden context
  -> primitive safe operational transition kernels
  -> HMM / belief-state organizational routing
  -> welfare / bottleneck optimization
  -> hard runtime boundary
  -> outcome / telemetry
  -> belief and transition-model update
```

Key 2026-08-27 findings:

- a finite 18-state `(context, workflow)` primitive chain generated an unbounded trajectory whose empirical occupancy approached its exact stationary distribution; at 800,000 steps the retained L1 occupancy error was `0.002692`;
- workflow state alone was not an exact first-order Markov sufficient statistic under persistent hidden context in the synthetic construction;
- HMM belief routing improved mean welfare over context-blind routing (`0.783482` vs `0.750517`) and improved context inference over current-observation-only routing (`73.18%` vs `59.11%`);
- a stale transition model reduced welfare and context inference, so transition-model freshness is itself a control concern;
- under an explicit context-transition drift, posterior-weighted online transition adaptation recovered late context accuracy from `69.44%` for a fixed stale HMM to `77.72%` with a small primitive support floor;
- a strong uniform primitivity mix harmed transition-model fidelity (`MAE 0.123956`), so primitivity should be enforced as a weak support/recovery constraint, not as high randomization;
- a naive equal-row online update was rejected because it over-updated low-posterior latent states.

Current interpretation:

> The workflow graph may be finite while its execution trajectory is unbounded. For a primitive finite operational chain, the relevant convergence is convergence of state distribution and empirical occupancy, not convergence of the state sequence to one state. Context that changes transition probabilities belongs in an augmented/hidden state; when hidden, the plugin should act on a belief state. Hard safety remains external to that learned belief and transition model.

## Current next questions

Probabilistic organization track:

1. adversarial / reward-hacked telemetry poisoning of online transition learning;
2. change-point detection versus continuous forgetting;
3. switching-cost-aware welfare optimization;
4. jointly learning workflow routing and hidden-context dynamics without collapsing recovery support.

Hard-runtime track:

1. independently sampled frozen/live LLM proposer;
2. real process/network/datastore failure semantics;
3. end-to-end remote idempotency/fencing and semantic binding.

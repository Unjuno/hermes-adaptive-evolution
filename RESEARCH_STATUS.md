# Research Status — 2026-08-27

The active research branch is `experiment/p0-runtime-closure`.

Start here:

1. [`docs/CURRENT_RESEARCH_STATE.md`](docs/CURRENT_RESEARCH_STATE.md) — retained hard-runtime architecture and findings through v15;
2. [`docs/EXPERIMENT_LEDGER_CURRENT.md`](docs/EXPERIMENT_LEDGER_CURRENT.md) — decision ledger through the v15 runtime gate;
3. [`docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md`](docs/SERIALIZED_TOOL_PARSER_BOUNDARY_2026-08-23.md) — latest completed serialized parser gate;
4. [`docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md`](docs/FINITE_WORKFLOW_INFINITE_CONTEXT_2026-08-27.md) — finite workflow / infinite ergodic trajectory and hidden-context organizational control;
5. [`docs/ONLINE_TRANSITION_ADAPTATION_2026-08-27.md`](docs/ONLINE_TRANSITION_ADAPTATION_2026-08-27.md) — online transition-model adaptation under context drift;
6. [`docs/PSM5_TWO_TIMESCALE_ADAPTIVE_ORGANIZATION_2026-08-27.md`](docs/PSM5_TWO_TIMESCALE_ADAPTIVE_ORGANIZATION_2026-08-27.md) — fast workflow mixing vs slower organizational self-update;
7. [`docs/PSM6_TELEMETRY_POISONING_RESISTANCE_2026-08-27.md`](docs/PSM6_TELEMETRY_POISONING_RESISTANCE_2026-08-27.md) — reward-hacked telemetry, verification, and quarantine;
8. [`docs/PSM7_SLEEPER_POISONING_VERIFIER_INDEPENDENCE_2026-08-27.md`](docs/PSM7_SLEEPER_POISONING_VERIFIER_INDEPENDENCE_2026-08-27.md) — delayed poisoning and verifier common-mode failure;
9. [`docs/PROBABILISTIC_ORGANIZATION_PROGRESS_2026-08-27_V2.md`](docs/PROBABILISTIC_ORGANIZATION_PROGRESS_2026-08-27_V2.md) — compact probabilistic-organization ledger;
10. [`docs/NEXT_ACTIONS.md`](docs/NEXT_ACTIONS.md) — frozen/live LLM proposer gate for the hard-runtime track.

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

A parallel organization-control track models the Prompt Supply Chain and agent placement as a finite stochastic workflow rather than a hand-written procedural loop.

Current retained model:

```text
finite workflow states
  + persistent hidden context
  -> primitive safe operational transition kernels
  -> HMM / belief-state organizational routing
  -> welfare / bottleneck optimization
  -> hard runtime boundary
  -> committed effect / telemetry
  -> evidence-weighted belief and transition-model update
  -> slower organizational-structure adaptation
```

Key 2026-08-27 findings:

- a finite 18-state `(context, workflow)` primitive chain generated an unbounded trajectory whose empirical occupancy approached its exact stationary distribution; at 800,000 steps the retained L1 occupancy error was `0.002692`;
- workflow state alone was not an exact first-order Markov sufficient statistic under persistent hidden context in the synthetic construction;
- HMM belief routing improved mean welfare over context-blind routing (`0.783482` vs `0.750517`) and improved context inference over current-observation-only routing (`73.18%` vs `59.11%`);
- a stale transition model reduced welfare and context inference, so transition-model freshness is itself a control concern;
- posterior-weighted online transition adaptation recovered part of an explicit context-transition drift, while strong uniform primitivity mixing harmed transition-model fidelity;
- a naive equal-row online update was rejected because it over-updated low-posterior latent states;
- PSM-5 found an intermediate structural-update cadence: period `5` reached welfare `0.872128`, above same-step `0.863106`, period `20` `0.823388`, and fixed `0.662210`; the sampled internal mixing proxy was about `1.5` steps, supporting a two-timescale interpretation rather than a fixed universal cadence;
- PSM-6 showed that coherent untrusted telemetry poisoning can move risky-context `execute` preference from `0.020` to `0.635` and increase hard-runtime block rate from `1.84%` to `11.30%`, while hard-executed unsafe effects remain `0` because safety is external;
- merely correcting sparse verified samples was insufficient at tested rates; disagreement-triggered `(context, workflow)` quarantine reduced risky-execute preference to `0.123` at 12% verification, but verified-only learning was utility-expensive;
- authoritative learning credit must bind to the committed/executed workflow identity, not the rejected proposal identity;
- PSM-7 delayed poisoning after a clean phase raised no-audit risky-execute preference from `0.026` pre-attack to `0.229` late; at nearly equal verifier-call budget, two independent verifiers ended at `0.149` versus `0.161` for perfectly common-mode failures, directional but not yet decisive evidence for verifier independence;
- permanent quarantine compresses long-run verifier-independence differences because any eventually clean audit can freeze a fixed surface pair, so the next adversary must mutate surface identity after quarantine.

Current interpretation:

> The workflow graph may be finite while its execution trajectory is unbounded. For a primitive finite operational chain, the relevant convergence is convergence of state distribution and empirical occupancy, not convergence of the state sequence to one state. Context that changes transition probabilities belongs in an augmented/hidden state; when hidden, the plugin should act on a belief state. Organizational transition learning is a slower adaptive layer and must not consume untrusted telemetry as authority. Hard safety remains external to both belief and learned transition structure.

## Current next questions

Probabilistic organization track:

1. adaptive attacker variants that mutate tool/resource/surface identity after quarantine;
2. semantic-intent grouping versus surface-pair quarantine;
3. temporary/change-point quarantine versus permanent bans;
4. online estimation of workflow mixing time and environment-drift time so structural update cadence can adapt;
5. jointly learning routing and hidden-context dynamics without collapsing recovery support.

Hard-runtime track:

1. independently sampled frozen/live LLM proposer;
2. real process/network/datastore failure semantics;
3. end-to-end remote idempotency/fencing and semantic binding.

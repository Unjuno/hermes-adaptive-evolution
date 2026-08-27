# Research Status — 2026-08-28

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
9. [`docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md`](docs/AGENT_PROMPT_CONTROL_SURFACE_2026-08-28.md) — Agent Prompt global leverage, provenance, break-even, and dual-axis optimization;
10. [`docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md`](docs/HUMIES_AGENT_PROMPT_CORE_V0_1.md) — experimental immutable Agent Prompt core contract;
11. [`docs/PROBABILISTIC_ORGANIZATION_PROGRESS_2026-08-28_V3.md`](docs/PROBABILISTIC_ORGANIZATION_PROGRESS_2026-08-28_V3.md) — compact organization + prompt-control ledger;
12. [`docs/NEXT_ACTIONS.md`](docs/NEXT_ACTIONS.md) — frozen/live LLM proposer gate for the hard-runtime track.

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

The organization-control track models the Prompt Supply Chain and agent placement as a finite stochastic workflow rather than a hand-written procedural loop.

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

Key retained findings:

- a finite 18-state `(context, workflow)` primitive chain generated an unbounded trajectory whose empirical occupancy approached its exact stationary distribution; at 800,000 steps the retained L1 occupancy error was `0.002692`;
- workflow state alone was not an exact first-order Markov sufficient statistic under persistent hidden context;
- HMM belief routing improved mean welfare over context-blind routing (`0.783482` vs `0.750517`) and context inference over current-observation-only routing (`73.18%` vs `59.11%`);
- stale transition models are a control concern; posterior-weighted online adaptation recovered part of context drift;
- strong uniform primitivity mixing harmed fidelity, so primitivity is retained as weak support/recovery rather than high randomization;
- PSM-5 found an intermediate structural-update cadence: period `5` reached welfare `0.872128`, above same-step `0.863106`, period `20` `0.823388`, and fixed `0.662210`; sampled internal mixing proxy was about `1.5` steps;
- PSM-6 showed untrusted telemetry poisoning can move risky-context `execute` preference from `0.020` to `0.635` and hard-runtime block rate from `1.84%` to `11.30%` while hard-executed unsafe effects remain zero because safety is external;
- sparse sample correction alone was insufficient; disagreement-triggered quarantine was more effective in the tested attack, while verified-only learning was utility-expensive;
- authoritative learning credit must bind to committed effect identity rather than rejected proposal identity;
- PSM-7 provides directional but not decisive evidence that verifier independence matters under delayed poisoning; surface-pair quarantine can compress the difference over long horizons.

## Agent Prompt control-surface track

The Agent Prompt is now modeled as an **orthogonal global behavior control surface**, not as part of the workflow transition kernel and not as a hard safety authority.

Retained architecture:

```text
immutable prompt core + versioned prompt patches
                |
                | global behavior prior
                v
probabilistic organization / transition kernel P_t
                |
                v
proposal / action
                |
                v
hard runtime boundary
```

Prompt evolution and transition-kernel evolution are separate control coordinates selected by downstream marginal value/cost.

Key APS findings:

- APS-1: prompt improvement was the best initial intervention in only `18.17%` of the base synthetic systems; adaptive marginal allocation reached welfare `0.893208`, above prompt-only `0.846131` and organization-only `0.891390`;
- APS-2: repeated destructive self-rewrite drove prompt clarity to `0.985` but source fidelity down to `0.532` and semantic failure to `7.68%`; immutable/versioned patch policies preserved source fidelity in the synthetic model;
- APS-3: prompt leverage has a measurable break-even regime; in the retained sweep, prompt was best for a majority starting at tested leverage scale `2.8`, rather than being universally first;
- APS-4: dual-axis adaptive allocation was best at every tested prompt-leverage scale (`0.7`, `1.3`, `2.8`, `4.5`), automatically shifting more budget to prompt as its leverage increased;
- APS-5: a strict immutable prompt-core assembler had `0` core overrides, `100%` attack rejection, and `0` normal false rejects over 60,000 synthetic patch cases, while naive last-writer-wins assembly allowed reserved-core override in `28.74%` of all mixed cases;
- `HUMIES_AGENT_PROMPT_CORE_V0_1.md` is an experimental prompt contract only; its real LLM benefit remains unverified.

Current interpretation:

> Prompt quality can have system-wide leverage because it affects behavior across workflow states, but global leverage does not imply that Prompt is always the current bottleneck. Prompt version/patch state and organizational transition state should therefore evolve independently, with an adaptive allocator comparing their downstream marginal value. Prompt evolution should preserve immutable source intent and provenance. Neither the prompt nor the learned transition model belongs in the hard safety TCB.

## Current next questions

Agent Prompt track:

1. independently sampled live/frozen LLM A/B test: baseline prompt vs immutable core vs core+patch vs sparse specialist annotations vs destructive rewrite;
2. estimate real downstream elasticity to prompt changes, including token/context cost;
3. online prompt-vs-transition bottleneck attribution under real Humies workload telemetry.

Probabilistic organization track:

1. mutating semantic sleeper attacks that change tool/resource/surface identity after quarantine;
2. semantic-intent grouping versus surface-pair quarantine;
3. temporary/change-point quarantine versus permanent bans;
4. online estimation of workflow mixing time and environment-drift time so structural update cadence can adapt;
5. jointly learning routing and hidden-context dynamics without collapsing recovery support.

Hard-runtime track:

1. independently sampled frozen/live LLM proposer;
2. real process/network/datastore failure semantics;
3. end-to-end remote idempotency/fencing and semantic binding.

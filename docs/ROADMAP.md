# Adaptive Evolution Roadmap

This is the forward-looking roadmap for `hermes-adaptive-evolution`. The project is intentionally **plugin-first**: Hermes remains the execution runtime and this repository provides an adaptive observation, evaluation, and later control layer.

## Design invariants

1. Use public Hermes plugin APIs before considering a core fork.
2. External Governor/budget/sandbox/permission boundaries are not weakened here.
3. Missing evidence means fallback or incomparable, never invented confidence.
4. Fine organization models always retain a coarse fallback.
5. Prediction loss and routing/decision loss are evaluated separately.
6. Candidate comparisons should be paired and task-stratified when possible.
7. Rare failures and recovery remain first-class metrics.
8. Synthetic sample counts never become production thresholds without real-Hermes calibration.

## M0 — Reproducible plugin and experiment substrate

**Status:** active / substantially complete.

Deliverables:
- installable Hermes plugin;
- metadata-first event recorder;
- deterministic normalizer/replay;
- unit tests and CI;
- explicit hypothesis/experiment ledger.

Exit: repository installs, tests, builds a wheel, and exposes the Hermes plugin entry point.

## M1 — Real Hermes E2E contract

**Priority:** P0.

Run a real Hermes trace containing:

```text
root agent
  -> delegate_task
  -> child agent
  -> tool success/failure
  -> recovery
  -> completion
```

Measure actual hook field coverage, duplicate/reorder/drop behavior, parent-child identity continuity, and observer overhead.

Exit: at least one real trace can be captured, normalized, exported, and replayed deterministically without a Hermes fork.

Fork gate: consider a core change only after documenting a decision-relevant primitive that cannot be observed or controlled through the public plugin surface.

## M2 — Organization State Estimator v0.1

Estimate observable organization state from real telemetry:

1. functional-role posterior and drift;
2. traffic-weighted role mixing;
3. directed interaction diffusivity/closure;
4. outcome/recovery fragility proxies;
5. local/higher-order residual structure only when justified.

Exit: at least one estimated state variable improves or safely gates held-out organization decisions relative to a context-only baseline.

## M3 — Finite-template task-conditioned router

Start with a small safe organization library. Do not mutate arbitrary graphs yet.

Decision form:

```text
expected utility under task-context uncertainty
- measured reconfiguration cost
- explicit risk/safety constraints
```

Exit: held-out net utility beats the best global template on a declared task distribution without rare-event regression.

## M4 — Rare-event monitor and controlled probes

Build coarse monitoring, residual-triggered high-resolution inspection, and externally gated low-risk system-identification probes.

Exit: materially better rare/cascade detection at acceptable false-escalation cost; probes remain optional and abortable.

## M5 — Adaptive organization search

Search coarse organization/order-parameter space first, then bounded local mutations, then policy/LoRA placement. Surrogates may advise but never permanently prune novel candidates on confidence alone.

Exit: adaptive search improves over the finite-template library while preserving safety/evaluation gates.

## M6 — Skill evolution

Keep Skills as explicit procedures. Evaluate Skill candidates with narrow benchmarks, regression, canary, promote/reject/rollback.

## M7 — Teacher and LoRA factory

Training data comes from **verified execution trajectories**, not raw Skill text. Separate clean success, recovery, preference/correction, and failure evidence. Candidate LoRAs require benchmark, Pareto comparison, lineage, canary, and rollback.

## M8 — Autonomous night loop

Integrate task generation, event-driven sensors, organization routing, Skill/LoRA candidates, repair, and externally enforced budget/sandbox limits.

Exit: long-running autonomous work can improve useful metrics while respecting hard external controls and preserving auditability.

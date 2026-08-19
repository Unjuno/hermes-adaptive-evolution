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
9. M1/M2 observation is hook-only; measurement should not alter the model-facing tool schema.
10. Organization topology is not forced into one scalar when falsification supports multiple order parameters.

## M0 — Reproducible plugin and experiment substrate

**Status:** implemented; continue regression hardening.

Deliverables:
- installable Hermes plugin;
- metadata-first event recorder;
- deterministic normalizer/replay;
- portable sanitized capture bundles;
- unit tests and CI;
- explicit experiment plan and compatibility contract;
- machine-readable CI and experiment result branches.

Exit: repository installs, tests, builds a wheel, and exposes the Hermes plugin entry point.

## M1 — Real Hermes E2E contract

**Priority:** P0.  
**Status:** provider-backed local-model path passed; repeatability and broader task coverage remain.

### Offline real-Hermes gate — passed

The dedicated contract path exercises real Hermes code without an external LLM call:

```text
real PluginManager discovery
  -> directory-plugin doctor
  -> pip entry-point discovery
  -> real delegate_task lifecycle
  -> real terminal tool error
  -> real terminal tool recovery
  -> session/API/skill/Kanban lifecycle dispatch
  -> observer SQLite
  -> capture bundle
  -> replay
  -> E1 field coverage
  -> E2 corruption experiment
```

### Provider-backed local-model gate — passed for LFM2.5 Q4

A real local model was run through Hermes on the deterministic repair fixture using the official LFM2.5-2.6B Q4_K_M GGUF through Ollama. The run contained:

```text
root
  -> delegate_task
  -> child
  -> tool failures
  -> same-agent recovery
  -> minimal counter.py repair
  -> passing unittest
```

The portable capture passed the E1 validator with clean parent/child identity and deterministic replay. This establishes the plugin observation path; it is **not** a general coding-quality benchmark.

A same-declared-context Qwen3 4B comparison currently fails before delegation with Hermes context-compression behavior. Treat that as a runtime/provider/model-metadata compatibility result until the context path is isolated; do not use it as a quality ranking.

Exit status: the minimum M1 exit condition is met. Keep a provider-backed E1 as a milestone regression gate, not a per-commit test.

Fork gate: no fork is justified by current evidence. Consider a core change only after documenting a decision-relevant primitive that cannot be observed or controlled through the public plugin surface and cannot be replaced by an equivalent observable.

## M2 — Organization State Estimator v0.3

**Status:** vector topology state implemented; real decision utility still unproven.

### Retained diagnostics

1. functional-role posterior/evidence/confidence;
2. confidence-gated traffic-weighted role mixing;
3. role-conditioned traffic coverage;
4. outcome/failure fragility proxy;
5. conservative identity uncertainty.

### Topology metric correction

The original start-only directed SLEM-gap `directed_diffusivity` was falsified on delegation-like DAGs and is retained only as a deprecated diagnostic.

Synthetic multi-target falsification supports at least two separate topology observables:

1. **directed traffic breadth** — local fan-out / how broadly sources distribute work;
2. **completed-flow connectivity** — global bottleneck/connectivity inferred only from relations with both start and stop evidence.

`interaction_completion_coverage` is exposed separately so missing returns cannot be silently treated as completed information paths.

This is intentionally a **vector state**, not a new single magic diffusivity scalar.

### Current hard gate

Run a provider-backed Hermes trace with multiple completed delegation edges and validate that the vector topology state is recoverable without identity ambiguity. The first target is a two-leaf star organization on the deterministic repair fixture.

Then test **decision usefulness**, not just reconstruction:
- compare context-only routing vs context + topology state;
- keep task seeds paired;
- keep task regimes stratified;
- use real completion/support uncertainty as a gate;
- evaluate routing regret and rare failure, not topology MSE alone.

Role-memory/change-point and macro-state/Markov falsification remain subsequent M2 experiments.

Exit: at least one estimated state variable improves or safely gates held-out organization decisions relative to a context-only baseline.

## M3 — Finite-template task-conditioned router

Start with a small safe organization library. Do not mutate arbitrary graphs yet.

Decision form:

```text
expected utility under task-context uncertainty
- measured reconfiguration cost
- explicit risk/safety constraints
```

Initial template axes should be coarse and observable, for example:
- one agent vs multiple agents;
- serial vs parallel delegation;
- local fan-out/breadth;
- completed-flow connectivity;
- reviewer/redundancy presence.

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

For LFM2.5-2.6B, keep deployment quantization separate from training quantization. Compare native/BF16 LoRA, 8-bit loaded LoRA, and 4-bit loaded QLoRA under the same verified-data budget. GGUF Q4 is an inference/deployment artifact, not the training checkpoint. See `experiments/LFM25_ADAPTATION_PLAN.md`.

## M8 — Autonomous night loop

Integrate task generation, event-driven sensors, organization routing, Skill/LoRA candidates, repair, and externally enforced budget/sandbox limits.

Exit: long-running autonomous work can improve useful metrics while respecting hard external controls and preserving auditability.

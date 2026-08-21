# Experiment Program v1 — Adaptive Knowledge Ecology

Status: active research program.

## 1. Goal

Build an adaptive multi-agent system in which useful behavioral knowledge survives, harmful/reward-hacking knowledge decays, new knowledge is generated after contradiction, and only sufficiently recurrent/verified patterns are later verbalized into explicit rules.

The program is not organized around one favorite mechanism. Experiments are prioritized by the uncertainty that blocks the next system-level design decision.

## 2. Current evidence ledger

### Supported in toy simulations

- Propagation is an amplifier, not a truth estimator.
- Delayed retention without independent re-verification does not remove reward hacks.
- Independent verification strongly reduces catastrophic propagation when verifier error is sufficiently low.
- Dense/high-speed propagation can outrun verification and amplify rare verification failures.
- Long memory can help preserve rare counterexamples, but long memory without forgetting creates adaptation inertia after environment shifts.
- Evidence-conditioned forgetting / knowledge-specific half-life can outperform one fixed memory horizon.
- Forgetting alone cannot discover missing alternatives; contradiction-triggered candidate generation can accelerate adaptation.

### Refuted / weakened

- “Repeated knowledge is probably true.” Refuted.
- “Longer retention is always better.” Refuted.
- “Centralized long-lived authority is automatically epistemically superior.” Refuted as a general claim.
- “A single topology scalar is sufficient for routing.” Previously refuted.

### Still unproven

- Whether these toy mechanisms transfer to LLM agents.
- Whether tacit trajectory retention beats immediate verbalization under equal information budgets.
- Whether useful functional roles and organization patterns emerge from behavior rather than being predeclared.
- Whether phase switching can be learned without becoming a meta-level reward-hack target.
- Whether a compact macro-state is sufficient for routing/organization decisions.

## 3. Experimental lanes

### Lane A — Knowledge ecology / world model (cheap container simulation)

Purpose: map causal structure and phase boundaries before spending model compute.

A1. Multi-factor portfolio screen: propagation rate × verification independence × forgetting × exploration trigger × phase controller.
A2. Verification-independence study with correlated failure domains and quorum rules.
A3. Dynamic phase control: fixed cycles vs risk-sensitive switching.
A4. Partial/contextual knowledge rather than binary true/hack knowledge.
A5. Candidate birth/death budget and redundancy control.
A6. Archive/curator mechanisms: persistence, rotation, federation, capture.

### Lane B — Tacit-to-explicit knowledge

B1. Equal-budget immediate verbalization vs raw trajectory retention vs delayed abstraction.
B2. Capacity control: equal retained bytes/tokens.
B3. Verifier control: immediate verbalization + verifier vs delayed + verifier.
B4. Formalization precision: does the verbal rule preserve the behavior that actually survived?

### Lane C — Role and organization emergence

C1. Infer functional role from action history without role names.
C2. Generate roles after repeated functional motifs rather than predefining roles.
C3. Measure organization phenotype from execution trajectories: depth, fanout, review edges, specialization, redundancy, communication density, latency, cost.
C4. Test whether phenotype/state improves held-out organization selection.

### Lane D — Fast LLM surrogate

Use official small quantized models only after a toy mechanism survives ablation.

D1. 350M-class screening on synthetic deterministic tasks.
D2. Repeat only effects that are robust across multiple task families/seeds.
D3. Reject surrogate-only effects that disappear under capacity controls.

### Lane E — Hermes / high-fidelity confirmation

Use only for mechanisms that already survive Lanes A-D.

E1. Runtime/instrumentation closure.
E2. Real multi-agent trajectory capture.
E3. Confirm selected retention/verification/organization policies at larger context/model size.

## 4. Compute allocation

Default allocation until contradicted by evidence:

- 70%: container/toy factorial and ablation work.
- 20%: small quantized LLM surrogate.
- 10%: Hermes/high-fidelity confirmation.

A narrow line of inquiry must not consume more than three consecutive experiment cycles without either (a) crossing a decision gate, (b) producing a new falsifiable hypothesis, or (c) being explicitly deprioritized.

## 5. Program-level decision gates

Gate G1 — Knowledge-selection mechanism
PASS only if verification + retention/forgetting beats propagation-only baselines under reward-hack and environment-shift stress.

Gate G2 — Search mechanism
PASS only if contradiction/uncertainty-triggered candidate generation beats constant random exploration at equal candidate-generation budget.

Gate G3 — Phase control
PASS only if adaptive switching improves the Pareto frontier of correct-knowledge prevalence, catastrophic hack risk, verification cost, and adaptation delay versus fixed schedules.

Gate G4 — Tacit retention
PASS only if delayed trajectory retention improves held-out transfer versus immediate verbalization without increasing false transfer/reward-hack persistence under equalized storage/compute budgets.

Gate G5 — Emergent organization
PASS only if behavior-derived role/organization state improves held-out decisions versus fixed templates and task-only routing.

Gate G6 — High-fidelity transfer
PASS only if at least one mechanism validated in cheap experiments reproduces directionally on LLM/Hermes tasks.

## 6. Next prioritized experiment queue

1. A1 multi-factor portfolio screen.
2. G2 equal-budget exploration trigger test.
3. A2 correlated verifier domains + quorum.
4. G3 adaptive phase controller with explicit verification-cost penalty.
5. B1/B2 tacit vs immediate abstraction under equal storage budget.
6. C1 role identifiability from behavior without role labels.
7. D1 small-model transfer only after at least two toy mechanisms survive.

## 7. Evaluation discipline

- Report absolute performance and failure rates, not only relative wins.
- Use paired randomness where possible.
- Separate mechanism discovery from confirmatory replication.
- Treat a toy PASS as hypothesis support, never as proof of LLM/system performance.
- Prefer Pareto analysis over one arbitrary weighted utility until weights have operational justification.
- Track negative results and invalid experiments explicitly.

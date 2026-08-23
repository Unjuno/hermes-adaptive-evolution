# Current Research State — 2026-08-23

## Core objective

Build an adaptive agent runtime that preserves useful autonomy while detecting, verifying, correcting, and ultimately hard-blocking only those state transitions that materially threaten future closed-loop behavior or explicit safety invariants.

The current working architecture is no longer a fixed organization chart or a prompt-only safety scheme. It is a layered runtime-control system:

```text
world / task
  -> stable base policy
  -> memory / representation / routing
  -> marginal future control-value estimate
  -> active-state deadband
  -> minimum useful intervention
  -> typed tool proposal
  -> authoritative security binding
  -> freshness/version check
  -> commit binding / transaction control
  -> certified fallback
  -> local hold
  -> independent capability suspension
  -> execution / outcome
  -> memory, trust, and transition-model update
```

## High-confidence retained findings

### Information routing and verification

- Sender-only routing becomes stale when receiver capability shifts.
- Receiver self-report is useful for compatibility but must not become final authority.
- Equal-budget negotiated routing is robust in ordinary noise/staleness, but can fail under strategic low-capability misreporting.
- Independent verification recovers that failure, but always-on verification is unnecessarily costly in benign regimes.
- Verifier count is not verifier independence: correlated/common-mode errors collapse quorum value.
- Verification should be triggered by both strategic-deception risk and epistemic uncertainty; attack prevalence alone is not a sufficient trigger.

### Hierarchical memory

- Universal recurrence-count promotion is rejected.
- Cross-context support and independent evidence must be separated from raw repetition.
- Promotion-time verification can become stale authority after environment drift.
- Contradiction-triggered re-verification sharply reduces stale high-level abstractions and demotion delay.
- Verification evidence therefore has a half-life; it is not permanent authority.

### Tacit vs explicit representation

- Raw/tacit trajectory retention is not universally superior to immediate verbalization.
- Clean stationary/drift regimes favor immediate explicit abstraction.
- When an attractive immediate proxy is systematically misaligned with delayed downstream truth, retaining recoverable trajectory detail before abstraction improves transfer and reduces reward-hack persistence.
- This advantage survives stronger explicit-memory controls and exists even when outcome delay is zero; the causal advantage is retained alternative explanatory detail, not waiting itself.
- Raw retention versus delayed abstraction is a storage Pareto problem: raw wins with ample capacity; delayed abstraction can win under tight memory budgets.

### Transition sensitivity and soft intervention

- Low immediate regret does not imply low future transition sensitivity.
- Random freedom in low-criticality states is unsafe; preserve a stable base policy instead.
- Transition-aware intervention strongly improves mimic/reward-hack conditions.
- Discrete role clusters did not beat role-free individual transition models; continuous functional neighborhoods were at least as good.
- Transition sensitivity alone over-intervenes in clean regimes.
- Hand-designed transition/trust multipliers improve this but still underperform direct marginal future control-value learning.

### Marginal future control value

- Directly learning counterfactual future control value is a better intervention target than adding hand-designed criticality terms.
- The target is sparse and heavily near-tied; exact intervention identity is not the right objective.
- A separately validated active-state deadband suppresses unnecessary clean intervention.
- Choosing the minimum intervention inside a near-optimal value set preserves utility while reducing controller influence.
- This operationalizes the early “escape energy” intuition as **minimum useful intervention intensity**, not as physical energy or state rarity.

### Hard safety envelope

- A statistical controller can have high mean utility while still producing rare invariant breaches.
- An independent hard envelope removes those breaches under its stated TCB assumptions, but is not free: conservative blocking costs utility.
- Capability compartmentalization reduces false blocks and blast radius relative to a single global reserve.
- Sparse high-assurance escalation can restore freedom, but guarantee strength depends on root independence and correctness.
- Signed metadata alone is insufficient: integrity and freshness are distinct; anti-rollback/monotonic version state is required.
- The trusted computing base can be reduced from a large protected metadata table to a small attested cache design containing trusted digest/version/root anchors.
- During root outage, stale signed metadata must not silently remain authoritative. Explicit degraded operation under an immutable coarse cap is safer than stale continuation and more useful than unconditional fail-closed.

### Fallback and terminal interlock

- Fallback failure must never re-enable the original unsafe proposal.
- Delayed central stop is not equivalent to an immediate local interlock.
- Cross-domain fallback improves reliability under common-mode failure but is not itself a hard guarantee.
- Ordinary execution failure and epistemic/integrity failure require different recovery state machines.
- Local hold can itself fail; an independent capability cut becomes the terminal safety boundary.
- If that cut is delayed or corrupted, the guarantee is lost. The guarantee is therefore conditional on a small, explicit TCB.

## Latest gate: typed tool-call transfer

The abstract hard-safety architecture has now been transferred to a mock typed-tool runtime with four classes:

- read-only lookup;
- bounded reversible write;
- irreversible delete;
- bounded transfer.

Key results from paired synthetic runs:

- actor self-reported safety fails under manipulation;
- a noisy statistical gate reduces failures but still leaks uncertified calls;
- a current authoritative typed gate removes retained leakage under the modeled conditions;
- a typed schema alone is insufficient if the actor can supply security-relevant attributes such as `protected=false`;
- security properties must be resolved from an external authoritative registry;
- stale typed metadata fails after policy drift;
- root outage benefits from explicit coarse degraded mode rather than stale continuation;
- terminal capability suspension must take effect before unsafe dispatch;
- validation and execution must be bound against TOCTOU races.

For TOCTOU controls, commit-time recheck is cheaper in low-contention regimes, while reservation/capability tokens become preferable when contention/race frequency is high enough to justify their fixed cost.

## Current architectural invariant

A useful concise statement is:

> **Parsing is not authorization. Typing is not authority. Integrity is not freshness. Validation is not commit. Redundancy is not independence. A statistical safety score is not a hard invariant.**

## Current uncertainty

The current evidence is still primarily synthetic. Important missing factors before claiming transfer to a real LLM agent include:

- serialized parser ambiguity and coercion behavior;
- duplicate/unknown fields;
- NaN/Inf/overflow/unit ambiguity;
- Unicode/confusable tool names;
- schema-version mismatch;
- replayed or mismatched capability tokens;
- real LLM stochastic proposal behavior;
- remote-tool transaction semantics;
- actual cryptographic implementation and hardware/runtime failure modes.

## Active priority

The next gate is the wire-format/parser boundary. Replace direct Python `Call` construction with serialized tool calls, attack the decoder, preserve authoritative metadata binding, and bind certification to commit. Only after that gate should a frozen/live LLM proposer be introduced over mock tools.

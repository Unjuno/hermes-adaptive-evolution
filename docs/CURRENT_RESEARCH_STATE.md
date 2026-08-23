# Current Research State — 2026-08-23 (v15)

## Core objective

Build an adaptive agent runtime that preserves useful autonomy while detecting, verifying, correcting, and hard-blocking only those state transitions that materially threaten future closed-loop behavior or explicit safety invariants.

## Current architecture

```text
world / task
  -> stable base policy
  -> memory / routing / representation
  -> marginal future control-value estimate
  -> active-state deadband
  -> minimum useful intervention
  -> serialized tool proposal
  -> bounded strict/canonical decoder
  -> authoritative security binding
  -> freshness / anti-replay state
  -> commit binding / anti-TOCTOU
  -> certified fallback
  -> local hold
  -> independent capability suspension
  -> execution / outcome
  -> memory, trust, and transition-model update
```

## High-confidence retained findings

### Routing / verification

- Sender-only routing becomes stale under capability shift.
- Receiver self-report can contribute compatibility evidence but must not become authority.
- Equal-budget negotiated routing is useful under ordinary noise/staleness but can fail under strategic low-capability misreporting.
- Independent verification recovers the extreme failure, but always-on verification is too costly in benign regimes.
- Verifier count is not verifier independence; common-mode errors collapse quorum value.

### Memory / abstraction

- Universal recurrence-count promotion is rejected.
- Cross-context support and verification must be separated from repetition.
- Verification evidence can become stale authority after drift and must be revocable.
- Raw/tacit retention is not universally better than immediate verbalization.
- When immediate proxy reward is systematically misaligned with downstream truth, preserving recoverable trajectory detail before abstraction can outperform immediate compression.

### Transition-sensitive control

- Low immediate regret does not imply low future transition sensitivity.
- Low-criticality operation should preserve a stable base policy, not randomize.
- Direct marginal future control-value learning beats hand-designed intervention multipliers in the tested toy mechanism.
- Counterfactual gain targets are sparse and near-tied; active-state gating and minimum near-optimal intervention reduce unnecessary controller influence.

### Hard safety / TCB

- High expected utility does not imply zero tail invariant violation.
- Statistical optimization and hard invariants belong to separate layers.
- Capability compartmentalization reduces conservatism and blast radius.
- Integrity and freshness are distinct; signed stale metadata is not current authority.
- A small attested cache can replace a much larger protected metadata table under the modeled assumptions.
- Root outage should transition to explicit degraded or fail-closed modes, not silent stale continuation.
- Fallback failure must never re-enable the original unsafe proposal.
- Local hold can fail; an independent capability cut is the terminal boundary in the current model.

### Typed tools / transactions

- Actor self-reported safety fails under manipulation.
- Security-relevant properties must be resolved from an external authoritative registry, not actor fields.
- Stale authorization state fails after policy drift.
- Check-then-use is vulnerable to TOCTOU; commit-time recheck or reservation is required depending on contention/cost.
- Terminal suspension must take effect before unsafe dispatch.

## Latest completed gate: serialized tool parser / wire boundary

The direct Python-call mock was replaced with serialized JSON-like proposals and attacked at the representation boundary.

Retained result from 64 paired seeds × 420 proposals, 32% malformed/adversarial payloads:

| policy | utility | unsafe leak | run violation |
|---|---:|---:|---:|
| lenient raw forwarding | 0.70853 | 0.123996 | 1.000 |
| strict schema only | 0.72565 | 0.017783 | 1.000 |
| strict + freshness | 0.74699 | 0 | 0 |
| explicit canonicalization + freshness | **0.78690** | **0** | **0** |

Mechanism conclusions:

- duplicate-field resolution can become a parser differential if gateway and executor disagree;
- NaN/non-finite values break naive comparison patterns;
- binary float can round `0.10000000000000001` to `0.1`, so hard decimal bounds require exact/fixed-precision comparison;
- schema version and units must be bound and canonicalized exactly once;
- actor-added security attributes remain outside the accepted schema and cannot override registry authority;
- strict schema validity does not prevent replay; one-shot freshness is a separate authorization property;
- explicit canonicalization can recover selected safe compatibility without forwarding the raw wire payload;
- payload size is bounded before parsing.

A fuzz-discovered implementation bug originally confused JSON arrays with the `object_pairs_hook` representation and caused uncaught exceptions. That implementation was invalidated. After introducing an explicit object marker, a 100,000-input malformed/random structural fuzz produced zero uncaught parser exceptions.

## Current architectural invariant

> **Parsing is not authorization. Typing is not authority. Integrity is not freshness. Validation is not commit. Canonicalization is safe only if the canonical object, not the raw ambiguous representation, is executed. A statistical safety score is not a hard invariant.**

## Current uncertainty

The evidence is still primarily synthetic. Important remaining factors include:

- actual cross-language parser/library behavior;
- cryptographic token implementation and distributed nonce consistency;
- remote tools that may reparse or reinterpret canonical calls;
- Unicode normalization of external resource identifiers;
- real LLM stochastic proposal distributions;
- context-window and retry behavior;
- real transaction semantics and infrastructure failure modes.

## Active priority

The parser gate is conditionally closed. Replace **only the proposer** with a frozen/live LLM over mock tools while keeping decoding, authority, freshness, commit, fallback, and suspension external to the model.

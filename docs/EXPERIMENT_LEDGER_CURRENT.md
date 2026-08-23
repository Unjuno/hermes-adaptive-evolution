# Experiment Decision Ledger — current through v15

This is a decision ledger, not a raw-result archive. It records which hypotheses survived matched controls, which claims were narrowed, and which implementation results were invalidated and rerun.

## Memory persistence / forgetting

Retained:
- indiscriminate long-lived memory can amplify reward-hacked evidence;
- rare counterexamples and independent evidence matter more than persistence alone;
- drift requires forgetting/decay; cumulative memory can create institutional inertia.

Rejected/qualified:
- “never forget” as a general principle;
- contradiction-triggered search as inherently superior before equal-budget controls.

## Information transfer / sender-receiver negotiation

Retained:
- equal-budget targeted routing beats broadcast in tested bandwidth-limited regimes;
- sender-only routing becomes stale after capability shift;
- receiver-side compatibility helps, but receiver self-report is not authority;
- negotiated routing is robust under ordinary noise/staleness but can fail under strategic low-capability misreporting;
- independent verification recovers that failure.

Rejected/qualified:
- broadcast advantage before bandwidth equalization;
- assuming accurate receiver self-knowledge;
- always-on verification as a benign default.

## Risk-triggered verification

Retained:
- conditional verification improves hard/stale/adversarial regimes;
- verifier quorum helps only when failure domains are sufficiently independent;
- attack prevalence alone is not a sufficient trigger because verification also corrects epistemic uncertainty.

Rejected:
- verifier count as a substitute for independence;
- a simple deception-EMA phase controller as a general scheduler.

Correction:
- an early common-error construction canceled during ranking and was invalidated; results were rerun with candidate-specific common-mode error.

## Hierarchical memory promotion / demotion

Retained:
- universal recurrence-count promotion over-generalizes local/reward-hacked knowledge;
- cross-context support, verification, and recurrence are separate evidence types;
- promotion-time verification can become stale authority;
- contradiction-triggered re-verification reduces stale high-level memory and demotion delay.

Decision:
- promotion, verification, and revocation are separate institutional functions;
- verification evidence has a half-life.

Correction:
- a demotion-latency metric lost state on eviction; that result was discarded and recomputed.

## G4 equal-budget tacit vs explicit memory

Rejected:
- universal superiority of tacit/raw retention.

Retained conditional result:
- clean regimes favor immediate abstraction;
- when immediate proxy reward is systematically misaligned with downstream truth, preserving recoverable trajectory detail before abstraction improves transfer and reward-hack robustness;
- the effect survives a stronger explicit archive and persists at zero outcome delay;
- raw retention vs delayed abstraction has a storage-capacity frontier.

Decision:
- representation format is an adaptive control choice.

## Transition sensitivity / role abstraction

Retained:
- low immediate regret does not imply low transition sensitivity;
- transition-aware intervention materially helps mimic/reward-hack worlds;
- low-criticality operation should preserve the stable base policy.

Rejected/uncertain:
- discrete role clustering as a distinct benefit; role-free individual/continuous functional representations were at least as good.

Qualified:
- transition sensitivity alone over-intervenes in clean worlds;
- hand-designed trust multipliers improve this but still miss the best fixed intervention envelope.

Decision:
- stop adding heuristic gain terms; learn marginal future control value directly.

## Marginal future control value / minimum useful intervention

Retained:
- direct counterfactual future control-value regression beats hand-designed transition/trust schedulers;
- clean/low-transition regimes can tie the base policy while mimic regimes tie the best tested fixed intervention envelope;
- gain targets are sparse and near-tied;
- an active-value deadband suppresses unnecessary intervention;
- selecting the minimum intervention in a near-optimal value set preserves utility while reducing controller influence.

Decision:
- operationalize the early “escape energy” idea as minimum useful intervention intensity, not state rarity.

## Hard safety envelope / TCB

Retained:
- high expected utility does not imply zero tail invariant violation;
- statistical optimization and hard invariants belong to separate layers;
- hard safety has a utility cost through conservative blocking;
- capability compartmentalization reduces false blocks and blast radius;
- sparse high-assurance escalation can recover freedom;
- common-mode root failure defeats naive redundancy;
- signed integrity does not imply freshness;
- anti-rollback/monotonic version state is required;
- a small attested cache can replace a much larger protected metadata table under the modeled assumptions;
- root outage should enter explicit degraded/fail-closed modes rather than silently using stale authority.

## Fallback failure / final interlock

Retained:
- fallback failure must never return to the original unsafe proposal;
- delayed central stop is not equivalent to immediate local hold;
- cross-domain fallback improves reliability but is not a hard guarantee;
- ordinary execution faults and integrity/freshness faults require different recovery paths;
- local hold can fail;
- an independent capability cut is the terminal boundary in the current toy model;
- if the cut is delayed/corrupted, the guarantee disappears.

Decision:
- guarantee claims must state the small trusted computing base explicitly.

## v14 typed tool-call transfer / transaction boundary

Mock tool classes:
- read-only lookup;
- bounded reversible write;
- irreversible delete;
- bounded transfer.

Retained:
- actor self-reported safety fails under manipulation;
- noisy statistical gating reduces but does not eliminate uncertified execution;
- security properties must be resolved from an authoritative external registry, not actor fields;
- stale typed metadata fails after policy drift;
- coarse degraded mode can outperform unconditional fail-closed during root outage while preserving modeled zero leakage;
- terminal capability cut must take effect before unsafe dispatch;
- check-then-use is vulnerable to TOCTOU;
- commit-time recheck is preferable at low contention while reservation/capability tokens become preferable when contention justifies their fixed cost.

Rejected:
- “typed API is enough”;
- “schema validity is authorization”;
- actor-owned security metadata;
- stale authorization state;
- validation without commit binding.

## v15 serialized tool parser / wire-format boundary

Main retained run:
- 64 paired seeds;
- 420 proposals/seed;
- 32% malformed/adversarial serialized proposals;
- 18 attack families covering duplicate/unknown/missing fields, coercion, bool-as-int, NaN/Inf, extreme/underflow magnitudes, negative zero, units, Unicode, version skew, security-field injection, token replay, precision smuggling, and oversized payloads.

Retained:
- permissive parsing plus raw forwarding is unsafe when gateway and executor parse the same wire representation differently;
- duplicate fields must not be silently resolved across a security boundary;
- NaN/non-finite values can defeat naive comparison logic;
- binary float can round a value slightly above a hard decimal bound down to the boundary; exact/fixed-precision comparison is required for security amounts;
- strict schema validity does not provide authorization freshness: replay alone broke strict-schema-only runs;
- one-shot nonce freshness closed replay in the retained benchmark;
- explicit canonicalization can recover selected safe compatibility (plain decimal strings, explicit unit conversion, negative-zero normalization) if raw input is discarded and only one canonical internal object proceeds;
- actor security fields remain excluded from the accepted schema;
- payload size is bounded before parse;
- schema/tool identifiers are exact rather than fuzzy/confusable.

Main outcomes:
- `lenient_raw`: utility 0.70853, unsafe leak 0.123996, run violation 100%;
- `strict_schema`: utility 0.72565, unsafe leak 0.017783, run violation 100%;
- `strict_fresh`: utility 0.74699, unsafe leak 0, run violation 0;
- `canonical_fresh`: utility 0.78690, unsafe leak 0, run violation 0.

Implementation correction:
- an early strict decoder confused JSON arrays with the `object_pairs_hook` object representation, producing uncaught `TypeError`/`ValueError` on malformed top-level arrays;
- that implementation was invalidated;
- after introducing an explicit object marker, 100,000 random malformed JSON values produced zero uncaught parser exceptions.

Decision:
- parser/wire gate PASS conditionally;
- schema validity, authorization freshness, and commit validity remain separate layers;
- stop local parser tuning and introduce a frozen/live LLM proposer without moving hard-boundary authority into the model.

## Active next gate

Replace only the synthetic proposer with a frozen/live LLM over mock tools. Keep the v15 decoder, authoritative registry, freshness/replay state, commit binding, fallback, and terminal suspension external to the model.

PASS only if model errors change availability/task success but cannot create an uncertified executable call on held-out adversarial prompt families.

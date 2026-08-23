# Experiment Decision Ledger — current through v14

This file is a decision ledger, not a complete raw-result archive. It records which hypotheses survived matched controls and which directions were rejected.

## 2026-08-21 to 2026-08-22: world-model and information-transfer controls

### Memory persistence / forgetting

Retained:
- Long-lived memory is not automatically good; persistent reward-hacked evidence can amplify bad policy.
- Rare counterexamples and independent evidence are more valuable than indiscriminate persistence.
- Environment shift requires forgetting/decay; cumulative memory creates institutional inertia.

Rejected or qualified:
- “Never forget” as a general memory principle.
- Contradiction-triggered candidate generation as inherently superior; its apparent benefit did not survive equal-budget exploration control.

### Information transfer

Retained:
- Equal-budget targeted routing beats broadcast in tested bandwidth-limited regimes.
- Fast transmission is valuable for warnings/immediate action; slower transmission can help abstract information when correction is possible.
- Fixed role labels become stale after capability shift.

Rejected or qualified:
- Broadcast advantage observed before bandwidth equalization.
- Extremely fine interaction-specific classification as universally better; it fragmented evidence and underperformed in sparse regimes.

## Sender/receiver negotiation

Initial pilot:
- negotiated sender shortlist + receiver compatibility outperformed random, sender-only push, and receiver-only pull in the original toy world.

Critical correction:
- the first negotiated implementation effectively granted unusually accurate receiver self-knowledge.

Robustness gate:
- equal candidate-query budgets were enforced;
- receiver noise, staleness, correlated error, latency cost, and strategic misreporting were introduced;
- verification-free negotiation failed under an intentionally extreme low-capability misreport attack;
- independent verification recovered positive net utility;
- always-on verification was too costly in benign regimes.

Decision:
- keep sender shortlist + receiver compatibility decomposition;
- do not treat receiver self-report as authority;
- make verification conditional and independently sourced.

## Risk-triggered verification

Retained:
- fixed local-risk verification improves net utility and harmful-transfer rate in hard/stale/adversarial regimes;
- verifier quorum helps only when failure modes are sufficiently independent;
- q=3 was a reasonable tested compromise, q=5 was not cost-justified in the current model;
- attack prevalence is not a sufficient verification trigger because verification also corrects epistemic uncertainty.

Rejected:
- simple deception-EMA phase controller as a general replacement for fixed thresholds;
- verifier count as a substitute for failure-domain independence.

Implementation correction:
- an early correlated-verifier model used a common error that canceled in ranking. Those results were invalidated and rerun with candidate-specific common-mode error within each quorum.

## Hierarchical memory promotion/demotion

Retained:
- universal recurrence-count promotion over-generalizes local/reward-hacked knowledge;
- promotion needs level-specific support, including cross-context evidence;
- independent verification is valuable when local reward may be deceptive;
- promotion-time verification can become stale authority after drift;
- contradiction-triggered re-verification materially reduces stale high-level memory and demotion delay.

Decision:
- verification evidence must be revocable and time-sensitive;
- promotion, verification, and revocation are separate institutional functions.

Evaluation correction:
- demotion-latency tracking originally lost state on eviction; that result was discarded and recomputed with external tracking.

## G4: equal-budget tacit vs explicit memory

Rejected:
- universal claim that tacit/raw trajectory retention is superior to immediate verbalization.

Retained conditional claim:
- clean stationary/drift regimes favor immediate abstraction;
- when immediate proxy reward is systematically misaligned with delayed downstream truth, keeping recoverable raw trajectory information before abstraction improves transfer and reduces reward-hack persistence;
- the advantage survives a stronger explicit archive that uses more actual memory cells and lookup cells;
- the advantage remains when outcome delay is zero, so “waiting” is not the causal mechanism;
- raw retention vs delayed abstraction has a capacity frontier.

Decision:
- representation format is an adaptive control choice, not a universal doctrine.

## Transition sensitivity / functional-role gate

Retained:
- low immediate regret does not imply low transition sensitivity;
- transition-aware intervention materially helps mimic/reward-hack worlds;
- low-criticality operation should preserve the stable base policy rather than randomize.

Rejected/uncertain:
- discrete role clustering as a distinct benefit. Behavior/trajectory role abstractions did not beat the role-free individual transition baseline.
- continuous trajectory-kNN beat discrete role clustering but only tied the individual transition baseline, including cold-start controls.

Qualified:
- transition sensitivity alone over-intervenes in clean worlds;
- independent proxy-bias evidence reduces over-intervention but a hand-designed multiplier still misses the best fixed intervention envelope.

Decision:
- stop adding heuristic gain terms; learn marginal future control value directly.

## Marginal future control value / minimum useful intervention

Retained:
- direct counterfactual future control-value regression outperforms hand-designed transition/trust schedulers;
- clean and low-transition regimes can statistically tie the base policy while mimic regimes tie the best tested fixed intervention envelope;
- counterfactual gain targets are sparse and near-tied;
- a separately validated deadband improves clean behavior by refusing low-value interventions;
- selecting the minimum intervention inside a near-optimal value set preserves utility while reducing average intervention.

Decision:
- operationalize “escape energy” as minimum useful intervention intensity, not state rarity or anomaly magnitude.

## Hard safety envelope

Retained:
- high expected utility does not imply zero tail invariant violation;
- an independent hard envelope can remove modeled breaches when its trusted base is correct;
- the hard layer has a cost: false blocks and utility loss;
- capability compartmentalization reduces conservatism and blast radius;
- sparse high-assurance escalation can recover freedom;
- common-mode root failure defeats naive redundancy.

Decision:
- statistical optimization and hard invariants belong to separate layers.

## TCB minimization / metadata freshness

Retained:
- signed integrity alone does not imply freshness;
- rollback/replay requires monotonic version or equivalent anti-rollback state;
- a small attested cache can reproduce the action trace of a much larger protected metadata table in the toy mechanism;
- root outage must not silently authorize stale metadata;
- an immutable coarse degraded mode can preserve zero modeled breach while recovering substantial utility relative to unconditional fail-closed.

Decision:
- guarantee claims must state the trusted computing base explicitly.

## Fallback failure / final interlock

Retained:
- fallback failure must never return to the original unsafe proposal;
- delayed central stop is not equivalent to immediate local hold;
- cross-domain fallback reduces common-mode operational failure;
- ordinary execution failure and integrity/freshness failure need different recovery paths;
- local hold can fail;
- an independent capability cut is the terminal safety boundary in the current model;
- if the cut is delayed or corrupted, the guarantee disappears.

Decision:
- the architecture is only as hard as its lowest enforcement point and the assumptions in its TCB.

## v14: typed tool-call transfer and transaction boundary

Mock tool classes:
- read-only lookup;
- bounded reversible write;
- irreversible delete;
- bounded transfer.

Retained:
- actor self-reported safety fails under manipulation;
- a noisy statistical gate reduces but does not eliminate uncertified execution;
- current typed external certification eliminates retained leakage under modeled conditions;
- stale typed metadata fails after policy drift;
- root-outage coarse degraded mode beats unconditional fail-closed while preserving modeled zero leakage;
- security-relevant fields supplied by the actor are unsafe even when schema-valid;
- protection class, capability class, policy version, and resource state must be resolved from an authoritative external registry;
- terminal capability cut must take effect before unsafe dispatch;
- check-then-use is vulnerable to TOCTOU;
- commit-time recheck is preferable in low-contention regimes, while reservation/capability tokens become preferable under sufficiently high contention when their fixed cost is justified.

Rejected:
- “typed API is enough”;
- “JSON/schema validity is authorization”;
- actor-owned security metadata;
- stale authorization state;
- validation without commit binding.

## Active next gate

Attack the serialized decoder boundary before introducing a real/frozen LLM proposer:

- duplicate and unknown fields;
- missing fields;
- coercion;
- NaN/Inf/overflow/negative-zero;
- unit ambiguity;
- schema-version mismatch;
- Unicode/confusable tool names;
- actor-injected security fields;
- replayed/stale/mismatched capability tokens.

PASS only if parser ambiguity cannot create an uncertified executable call and authorization remains bound to authoritative state and commit.

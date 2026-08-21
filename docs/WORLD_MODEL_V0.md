# World Model v0: Knowledge Ecology, Delayed Feedback, and Institutions

Status: working model, not a historical claim.

## 1. Core ontology

The system is modeled as a knowledge ecology rather than a fixed organization chart.

- **Agent**: local actor with private experience and a behavioral policy.
- **Candidate knowledge**: a reusable behavioral pattern that may be correct, context-limited, or reward-hacking.
- **Propagation edge**: a temporary contact through which a candidate pattern can spread.
- **Verification edge**: an independently sampled path used to test a candidate under a different condition.
- **Archive / curator**: a persistent state that preserves delayed outcomes and rare counterexamples across time.
- **Formalization**: a later compression step that turns stable tacit patterns into explicit rules or definitions.
- **Institution**: a mechanism that controls propagation, verification, persistence, and authority weight over time.

## 2. Current causal picture

```text
experience
  -> candidate tacit pattern
  -> local reuse
  -> random propagation
  -> independent verification
  -> survive / decay
  -> repeated cross-context recurrence
  -> archive
  -> delayed formalization
```

Propagation is not treated as truth estimation. It is an amplifier. A candidate can spread because it is useful, fashionable, locally rewarded, or reward-hacking.

Verification must therefore remain at least partially independent from propagation.

## 3. Phase-switching hypothesis

The organization does not need to remain globally synchronized.

A useful architecture may alternate between:

1. **Propagation phase**: sparse or random contacts, fast reuse, exploration.
2. **Verification phase**: independent checks, counterfactual or rare-context tests, decay of failed candidates.
3. **Archive phase**: preserve delayed outcomes and rare failures long enough to detect patterns that short-lived agents miss.
4. **Formalization phase**: only after recurrence and verification, compress a pattern into explicit knowledge.

The phase controller itself is a later research target and must be resistant to meta-level reward hacking.

## 4. Institutional archetypes to test

Historical labels are not used as direct optimization targets. We instead isolate mechanisms that historical institutions may instantiate.

### A. Peer ecology

- no central archive
- random local transmission
- local verification
- low catastrophic authority failure, but weak long-delay integration

### B. Long-lived curator

Mechanisms loosely motivated by long-tenure centralized institutions:

- persistent memory across many delayed outcomes
- stable aggregation rules
- ability to preserve rare counterexamples
- strong broadcast authority

Potential benefit: delayed feedback can be integrated over a longer horizon.

Potential failure: one correlated error, capture, or reward hack can be amplified by authority.

### C. Rotating curator

- shorter institutional memory
- lower long-term lock-in
- greater loss of delayed evidence

### D. Federated curators

- multiple archives / failure domains
- weaker individual authority
- quorum or majority recommendation
- better resistance to single-point capture, at the cost of slower convergence

## 5. Historical hypothesis: monarchy-like persistence

A narrow, testable hypothesis is allowed:

> Some long-lived centralized regimes may have gained an informational advantage from persistent institutional memory and long feedback horizons.

This is **not** equivalent to any of the following claims:

- monarchy is globally optimal;
- longevity proves quality;
- coercive survival is evidence of epistemic performance;
- historical persistence implies modern suitability.

Longevity is confounded by military power, inheritance rules, path dependence, extraction capacity, geography, coercion, demographic structure, and survivorship bias.

The simulator therefore tests the mechanism **long-lived archive + authority**, not the political label itself.

## 6. First simulation result

Toy environment:

- a true rule is moderately successful across both common and rare contexts;
- a reward-hacking rule is more successful in common contexts but fails in rare/counterfactual contexts;
- feedback is delayed;
- social propagation favors the locally attractive hack;
- institutional variants differ in memory horizon, verification weighting, federation, and authority.

Initial container screening showed:

- long memory over **raw average reward alone** did not help and could amplify the hack;
- long memory became useful when the archive preserved and up-weighted independent rare-context evidence;
- rotating short memory lost much of that advantage;
- federation reduced single-point catastrophic authority risk.

Thus the current hypothesis is more specific:

> Persistence is useful only when the persistent institution stores discriminating evidence. Long tenure without independent verification is not epistemically sufficient.

## 7. Next implementation targets

1. Replace binary true/hack knowledge with context-dependent partial knowledge.
2. Separate propagation graph from verification graph.
3. Add adaptive propagation/verification phase switching.
4. Model correlated verifier failures and institutional capture.
5. Add archive compression and delayed formalization.
6. Add regime shifts so old knowledge can become obsolete.
7. Measure adaptation latency, catastrophic takeover probability, knowledge diversity, and false formalization rate.

## 8. Falsification criteria

The long-lived-curator hypothesis should be rejected if, after controlling for verification quality and evidence volume, longer persistence does not improve delayed-feedback adaptation or if its authority-induced failure risk dominates the benefit.

The broader knowledge-ecology hypothesis should be rejected if independent verification and delayed retention provide no out-of-sample advantage over simpler immediate-memory baselines under matched compute and observation budgets.

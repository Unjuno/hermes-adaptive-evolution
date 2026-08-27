# Probabilistic Organization Progress — 2026-08-27 v2

Retained:
- finite workflow / infinite trajectory: primitive augmented chain occupancy converges in the synthetic model;
- hidden context materially improves organizational routing when workflow state alone is not Markov-sufficient;
- fixed HMM transition models become stale after context drift;
- posterior-weighted online transition adaptation recovers part of the drift gap;
- strong uniform primitivity mixing harms model fidelity; weak support constraints are preferred;
- PSM-5: structural update cadence has an intermediate optimum in the tested system; update period 5 outperformed 1, 20, 80, and 240 while internal mixing proxy was ~1.5 steps;
- PSM-6: untrusted telemetry can reward-hack the learned organization while hard safety remains intact;
- sparse sample correction is insufficient under coherent poisoning;
- disagreement-triggered quarantine is more effective than correction-only at low verification rates, but adds utility/coverage tradeoffs;
- authoritative learning credit must bind to committed effect identity, not rejected proposal identity.

Next:
1. delayed/sleeper telemetry poisoning and verifier common-mode corruption;
2. online change-point detection vs permanent quarantine;
3. estimate mixing-time / drift-time ratio online and adapt structural update cadence;
4. integrate these mechanisms into the Humies Prompt-Supply-Chain plugin contract without moving hard authority into the learned controller.

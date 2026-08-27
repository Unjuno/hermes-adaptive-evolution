# PSM-7 — Sleeper Poisoning and Verifier Independence — 2026-08-27

## H
After a clean trust-building phase, delayed telemetry poisoning can reshape the learned organization. At equal verifier-call budget, independent verifier failures should contain the attack better than perfectly common-mode failures.

## T
- episodes: 1,800
- steps/episode: 1100
- delayed attack starts at step 700
- single-verifier audit rate: 6%
- double-verifier event rate: 3%; two verifier calls/event, approximately equal call budget
- per-verifier corruption probability on poisoned samples: 80%
- hard unsafe execution remains externally blocked.

## Results

| Policy | Pre execute pref | Early post | Late execute pref | Hard-block rate | Verifier calls/episode |
|---|---:|---:|---:|---:|---:|
| no_audit | 0.026 | 0.040 | 0.229 | 3.385% | 0.0 |
| single_clean | 0.056 | 0.077 | 0.117 | 3.250% | 65.8 |
| single_common_corrupt | 0.056 | 0.075 | 0.128 | 3.294% | 65.8 |
| double_independent | 0.043 | 0.060 | 0.149 | 3.196% | 65.8 |
| double_common | 0.043 | 0.059 | 0.161 | 3.284% | 65.8 |

## D

No-audit late risky-execute preference rose to **0.229** after the sleeper attack.

At nearly identical verifier-call budgets:
- double independent verifier: late preference **0.149**
- double common-mode verifier: late preference **0.161**

The independent pair also generated more quarantine evidence (1.168 vs 0.977 events/episode).

This is **directional but small evidence**, not a decisive confirmation. Permanent quarantine makes eventual detection likely even with high corruption, so the long-horizon difference is compressed.

Retained interpretation:
> verifier count and verifier independence remain distinct variables in probabilistic organization learning, but the current sleeper benchmark is not yet strong enough to estimate the value of independence precisely.

## Negative / invalidated precursor
The first PSM-7 screen used 40% corruption and a long post-attack horizon. Permanent quarantine erased most common-mode differences once any clean audit eventually occurred. It was not used to claim verifier-independence value. The retained v0.2 stresses 80% corruption and a shorter post-attack horizon.

## C
A stronger adaptive attacker can change surface identity after quarantine, making eventual detection of one fixed `(context, workflow)` pair irrelevant. This may amplify the benefit of semantic-intent grouping and independent verification.

## U
Next:
1. attack variants that mutate tool/resource/surface identity after quarantine;
2. temporary/change-point quarantine instead of permanent bans;
3. correlated verifier failures over semantic intent, not just samples;
4. compare semantic-intent locator + independent verifier to surface-pair quarantine.

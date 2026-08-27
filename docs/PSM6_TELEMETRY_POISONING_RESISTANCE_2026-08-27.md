# PSM-6 — Telemetry Poisoning and Reward-Hack Resistance — 2026-08-27

## H
If the organization transition model learns directly from untrusted outcome telemetry, an adversary can reshape the Prompt-Supply-Chain / agent-placement distribution even when a separate hard runtime prevents the unsafe effect itself.

## Attack
After step 250, in risky context:
- dangerous `execute` proposals receive a positive telemetry bonus of 1.6;
- `audit` and `recover` receive a negative telemetry penalty of 1.0;
- poisoning probability is 75%;
- spot verification rate is 12%.

The hard runtime still blocks risky `execute` before effect, so hard-executed unsafe rate remains zero by construction. The target is the **learned organization**, not the hard invariant.

## Main results

| Policy | Welfare | Hard-block action rate | Late risky-execute preference | Late audit+recover preference |
|---|---:|---:|---:|---:|
| clean_untrusted | 0.867060 | 1.840% | 0.020 | 0.725 |
| trusted_authoritative | 0.863230 | 4.092% | 0.124 | 0.636 |
| naive_poisoned | 0.854935 | 11.304% | 0.635 | 0.074 |
| clipped_poisoned | 0.843072 | 4.313% | 0.128 | 0.120 |
| verified_only_poisoned | 0.767707 | 5.078% | 0.156 | 0.415 |
| verified_correct_poisoned | 0.855292 | 10.990% | 0.613 | 0.091 |
| quarantine_poisoned | 0.850455 | 4.458% | 0.123 | 0.239 |

### Core negative result

Clean untrusted learning converged to risky-execute preference **0.020**.
Under coherent telemetry poisoning, naive learning moved it to **0.635** and increased hard-runtime block rate from **1.84%** to **11.30%**.

Therefore:
> Hard safety can remain intact while adaptive organization learning is reward-hacked into repeatedly proposing actions that the hard boundary must reject.

This creates cost, churn, and degraded organizational quality even without an unsafe effect.

### Verification is not automatically sufficient

At 12% verification, merely replacing verified samples with authoritative outcomes left risky-execute preference at **0.613**.

Verified-only learning suppressed poisoned credit but reduced welfare to **0.768**, showing the expected sparse-evidence cost.

Disagreement-triggered quarantine reduced risky-execute preference to **0.123** while using about 131.8 verified samples per episode.

## PSM-6b — Verification-rate sweep

| Verify rate | Correct-only execute pref | Quarantine execute pref | Quarantine welfare |
|---:|---:|---:|---:|
| 2% | 0.595 | 0.252 | 0.837625 |
| 5% | 0.577 | 0.159 | 0.837221 |
| 10% | 0.570 | 0.129 | 0.836451 |
| 20% | 0.547 | 0.131 | 0.836444 |
| 40% | 0.454 | 0.142 | 0.834817 |

In this screening model, quarantine improved sharply from 2% to 5–10% verification, while 20–40% verification produced little additional execute-preference reduction and more quarantine events.

## Invalidated precursor
An earlier reward-poisoning screen credited the reward of a hard-runtime `recover` fallback back to the rejected `execute` proposal. That incorrectly made authoritative telemetry reinforce the rejected proposal. The run was invalidated.

Retained credit rule:
> authoritative outcome credit attaches to the **committed/executed workflow identity**, not the original rejected proposal identity.

This is the learning analogue of `validation != commit` and `proposal identity != effect identity`.

## D
- naive learning from untrusted telemetry: **FAIL**;
- clipping alone: **FAIL / insufficient**;
- sparse sample correction alone: **FAIL / insufficient at tested rates**;
- verified-only: **safe from poison credit but utility-expensive**;
- disagreement-triggered quarantine: **provisional positive result**;
- hard runtime remains independent and blocks unsafe execution throughout.

## C
The strongest competing hypothesis is that real telemetry attacks will be subtler and evade simple disagreement thresholds, especially if the attacker also influences the verifier or downstream proxy reward.

## U
Next gate:
1. common-mode verifier corruption;
2. delayed poisoning that first builds trust;
3. change-point detector vs permanent quarantine;
4. separate trusted transition evidence from ordinary welfare evidence.

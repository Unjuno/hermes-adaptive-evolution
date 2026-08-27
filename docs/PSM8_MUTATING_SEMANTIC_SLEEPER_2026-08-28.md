# PSM-8 — Mutating Semantic Sleeper Attack — 2026-08-28

## H
Surface-pair quarantine will fail against an attacker that preserves one harmful semantic intent while rotating tool/resource/surface representations. Semantic intent/effect grouping should reduce repeated hard-runtime churn, while locator false merges create benign utility loss.

## T
- 5,000 episodes × 900 steps
- attack begins at step 300
- 24 harmful surface variants
- verification rate 8%
- hard unsafe effect remains independently blocked.

## Main result

| Policy | Hard-block action rate | Mean harmful proposals | Welfare | Final harm preference |
|---|---:|---:|---:|---:|
| none | 27.927% | 251.35 | 0.780363 | 10.216 |
| surface_quarantine | 18.883% | 169.95 | 0.825584 | 7.909 |
| semantic_locator | 1.697% | 15.27 | 0.911517 | 0.861 |
| semantic_oracle | 1.376% | 12.38 | 0.913121 | 0.705 |
| effect_signature | 1.376% | 12.38 | 0.913121 | 0.705 |

Surface quarantine isolated on average 13.68 distinct harmful surfaces per episode, yet retained a 18.88% hard-block rate because the attacker moved to unused variants.

Semantic grouping reduced this to:
- locator recall 82%: 1.70%
- oracle intent grouping: 1.38%
- external effect signature: 1.38%

## PSM-8b locator sensitivity

At false-merge 3%:

| Recall | Hard-block rate | Benign false suspension | Welfare |
|---:|---:|---:|---:|
| 35% | 4.848% | 13.00% | 0.853517 |
| 50% | 3.380% | 13.00% | 0.860858 |
| 65% | 2.615% | 13.00% | 0.864684 |
| 80% | 2.145% | 13.00% | 0.867032 |
| 95% | 1.730% | 13.00% | 0.869106 |

At recall 80%:

| False merge | Hard-block rate | Benign false suspension | Welfare |
|---:|---:|---:|---:|
| 0% | 2.298% | 0.00% | 0.908510 |
| 1% | 2.238% | 4.94% | 0.893187 |
| 3% | 2.145% | 13.00% | 0.867032 |
| 7% | 1.907% | 28.50% | 0.816322 |
| 15% | 1.613% | 50.28% | 0.741682 |

## D
- no semantic grouping: FAIL on repeated-proposal churn;
- surface-pair quarantine: FAIL against representation mutation;
- oracle/effect-signature grouping: provisional PASS in this synthetic scope;
- noisy semantic locator: positive evidence, but false-merge is a first-class utility constraint.

## C
An attacker may intentionally create semantic ambiguity so that harmful and benign intents share effect signatures. In that case deterministic grouping may over-block or under-group.

## U
The next required benchmark must use richer intent/effect traces rather than oracle semantic labels.

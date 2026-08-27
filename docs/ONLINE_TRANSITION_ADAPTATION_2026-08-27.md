# Online Transition Adaptation under Context Drift — 2026-08-27

## Question

Can the probabilistic organizational controller adapt its hidden-context transition model after environment drift while preserving a primitive operational kernel?

## Setup

- hidden contexts: 3
- workflow states: 6
- episodes: 5,000
- steps/episode: 700
- transition-regime drift at step 300
- noisy telemetry emissions
- hard unsafe execution remains externally blocked

The adaptive estimator uses posterior-weighted expected transition counts with exponential forgetting.

## Results

| Policy | Late context accuracy | Late welfare | Transition MAE | Minimum transition p | Late hard-block rate |
|---|---:|---:|---:|---:|---:|
| observation only | 59.295% | 0.819874 | 0.080000 | 0.01 | 9.747% |
| fixed stale HMM | 69.438% | 0.820544 | 0.080000 | 0.01 | 8.920% |
| adaptive, no floor | 77.181% | 0.823250 | 0.052222 | 0.000118728 | 7.377% |
| adaptive + 0.003 primitive mix | 77.716% | 0.822624 | 0.040492 | 0.00208254 | 7.564% |
| adaptive + 0.03 primitive mix | 77.229% | 0.820687 | 0.123956 | 0.01 | 8.316% |
| slow adaptive + 0.03 mix | 74.117% | 0.820361 | 0.051428 | 0.01 | 8.973% |
| oracle model switch | 79.100% | 0.822772 | 0.000000 | 0.01 | 7.239% |

## Main findings

### 1. A fixed HMM becomes stale after drift

Fixed-HMM late context accuracy: **69.438%**.
Its late transition MAE remains **0.0800**.

### 2. Posterior-weighted online adaptation recovers part of the gap

With a small primitive floor (`0.003` mix):
- late context accuracy: **77.716%**
- late transition MAE: **0.0405**
- late welfare: **0.822624**

Oracle context-model switch remains higher in context accuracy at **79.100%**.

### 3. Heavy primitivity regularization is harmful

A `0.03` uniform primitive mix forces every transition to retain broad support, but it biases the learned transition kernel:
- transition MAE rises to **0.1240**;
- late welfare falls to **0.820687**.

Therefore:

> primitivity is a support / recurrence constraint, not a command to make the workflow highly random.

A small positive support floor can preserve recurrence while allowing sharply non-uniform organizational behavior.

### 4. Unfloored adaptation has a different risk

The unfloored estimator performs well in this finite experiment, but its minimum learned transition probability fell to **0.000118728**.
It remained mathematically positive here, but continued adaptation could effectively eliminate recovery paths numerically or under thresholding.

## Invalidated precursor

A preceding naive update normalized every latent-state row equally at each step. Low-posterior rows were therefore updated as strongly as likely rows, causing transition MAE to become much worse than the fixed stale model. That mechanism was rejected and replaced with posterior-mass-weighted expected transition counts.

The negative result is retained as evidence that online self-evolution needs evidence-weighted transition updates.

## Decision

### H
A finite primitive workflow can adapt its transition probabilities online after context drift without explicit procedural loops, provided transition updates are weighted by posterior evidence and primitivity is enforced as a weak support constraint rather than strong uniform randomization.

### D
- fixed transition model under drift: **FAIL / stale**;
- naive equal-row online update: **FAIL**;
- posterior-weighted adaptive HMM: **positive evidence**;
- small primitive support floor: **provisional PASS**;
- aggressive primitive mixing: **FAIL on model fidelity / welfare**;
- learned transition model as hard authority: **not allowed**.

### C
The main competing hypothesis is that apparent adaptation depends on the stationary piecewise-Markov construction; real Humies context may drift continuously or strategically, making exponential forgetting insufficient.

### U
Next uncertainties:
1. adversarial / reward-hacked telemetry poisoning of transition learning;
2. change-point detection versus continuous forgetting;
3. switching-cost-aware welfare optimization;
4. learning workflow transition policy and hidden context dynamics simultaneously.

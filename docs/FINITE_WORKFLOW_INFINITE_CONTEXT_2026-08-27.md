# Finite Workflow × Infinite Contextual Trajectory — 2026-08-27

## Research question

Can a finite Humies workflow/organization be represented as a stochastic transition model whose **infinite execution trajectory** converges in empirical occupancy, while hidden context determines adaptive agent placement without hand-written retry loops?

## Precise claim

For a finite primitive Markov chain with transition matrix `K`, the state sequence itself does **not** converge to one state. Rather:

1. the distribution over states converges to a unique stationary distribution `pi`;
2. along one ergodic infinite trajectory, empirical state frequencies converge almost surely to `pi`.

If workflow transition probabilities depend on persistent context that is not directly observed, workflow state alone need not be first-order Markov. Augmenting state with context restores a finite Markov representation when the context process itself is finite-state Markov. With hidden context, filtering produces a belief-state controller (HMM/POMDP view).

## Model

Hidden contexts:
- normal
- ambiguous
- risky

Workflow states:
- ingest
- tune
- audit
- specialist
- execute
- recover

Augmented state count: 18.

Each context-specific operational workflow kernel is primitive; the joint `(context, workflow)` chain is also primitive.

### Variables

| Symbol | Meaning | Unit | Domain / type |
|---|---|---|---|
| `z_t` | hidden context | none | finite categorical |
| `w_t` | workflow / organizational state | none | finite categorical |
| `K` | augmented transition kernel | none | row-stochastic matrix |
| `b_t` | posterior belief over hidden context | none | probability simplex |
| `r(z,w)` | state welfare | normalized utility | scalar |
| `pi` | stationary occupancy distribution | none | probability simplex |
| `T` | trajectory length | steps | positive integer |

Long-run welfare:

`W_bar = sum_{z,w} pi(z,w) r(z,w)`.

Dimension check: `pi` is dimensionless probability and `r` is normalized utility, so `W_bar` has the same utility unit as `r`.

## Structural result

- context-kernel primitive exponent: 1
- each workflow-kernel primitive exponent: 1
- joint-chain primitive exponent: 1
- joint spectral gap: 0.071270
- oracle joint stationary welfare: 0.802185

## Single infinite-trajectory approximation

Empirical occupancy error relative to the exact stationary distribution:

| Steps | L1 occupancy error | Max absolute error |
|---:|---:|---:|
| 1,000 | 0.241695 | 0.046091 |
| 5,000 | 0.077136 | 0.017291 |
| 20,000 | 0.027799 | 0.005741 |
| 100,000 | 0.017002 | 0.005601 |
| 400,000 | 0.004197 | 0.000626 |
| 800,000 | 0.002692 | 0.000502 |

The 800,000-step L1 occupancy error is **0.002692**.

This directly supports the finite-workflow / infinite-trajectory interpretation in this modeled primitive chain.

## Context-aware organizational control

Paired experiment:
- episodes: 24,000
- steps/episode: 320
- same hidden context worlds across controllers
- hard unsafe execution remains outside the stochastic controller

| Controller | Mean welfare | Context inference | Raw unsafe action rate | Hard executed unsafe |
|---|---:|---:|---:|---:|
| deterministic loop | 0.682725 | — | 3.589% | 0.0% |
| context blind | 0.750517 | — | 4.282% | 0.0% |
| current observation only | 0.774957 | 59.108% | 2.534% | 0.0% |
| HMM belief | 0.783482 | 73.182% | 2.628% | 0.0% |
| HMM, 50% stale model | 0.770281 | 64.626% | 2.734% | 0.0% |
| oracle context | 0.816040 | — | 1.505% | 0.0% |

Key comparisons:
- context blind -> HMM welfare gain: **+0.032965**
- observation-only -> HMM welfare gain: **+0.008525**
- HMM -> oracle remaining gap: **0.032559**
- fresh HMM -> 50% stale HMM welfare loss: **0.013201**

HMM context inference accuracy was 73.182%, compared with 59.108% for current observation alone.

## Does context actually matter for the Markov state?

The measured weighted L1 change in next-workflow distribution after additionally conditioning on the previous workflow was:

**0.070708**

A non-zero value is evidence that workflow state alone is not an exact first-order Markov sufficient statistic in this persistent-hidden-context construction.

The finite Markov state is therefore not merely `workflow`; it is at least the augmented `(context, workflow)` state. When context is hidden, the controller acts on the belief `b_t`.

## Decision

### H

A finite set of workflow states can support unbounded autonomous execution without procedural loop code if recurrent behavior is represented by a primitive stochastic transition kernel; persistent context should be represented as an augmented/hidden state when it changes transition probabilities.

### T

- exact stationary distribution of the 18-state augmented chain;
- one 800,000-step trajectory;
- 24,000 paired 320-step controller episodes;
- deterministic loop, context-blind Markov, observation-only, HMM belief, stale-HMM, and oracle-context controls;
- hard unsafe execution blocked externally.

### D

- finite primitive workflow -> infinite empirical occupancy convergence: **PASS in this model**;
- deterministic fixed loop as organization controller: **inferior welfare**;
- context-blind controller: **inferior to HMM and oracle**;
- fresh HMM belief: **positive result**;
- stale HMM transition model: **negative result / freshness requirement**;
- learned belief as hard authority: **not tested and not permitted by architecture**.

### C

Strong competing hypotheses:
1. the real Humies organizational process may be non-stationary enough that a fixed transition kernel never remains valid long enough to mix;
2. latent context may require a much larger or continuous state than a small HMM;
3. welfare optimization may drive excessive organizational switching unless switching cost is included.

### U

The next major unknown is whether an online-adaptive transition model can track context drift without becoming unstable or reward-hacked.

## Architectural consequence

The proposed plugin now has three distinct layers:

1. **Hard runtime kernel** — invariants, authority, commit, idempotency;
2. **Probabilistic organizational dynamics** — finite workflow graph, primitive safe operational kernels, hidden context / belief;
3. **Welfare and bottleneck optimizer** — updates transition probabilities, agent placement, and specialist routing subject to the hard kernel.

The stochastic organizational layer replaces explicit retry loops with transition dynamics, but it does not replace the hard safety layer.

# BAC-19 / BAC-20 — Latent Synthesis and Representation Lifecycle — 2026-08-28

## H
When the current representation is structurally insufficient, a useful latent control coordinate can be synthesized from raw primitives. Redundant born representations should be logically merged while preserving constituent provenance so later semantic drift can be isolated and retired.

## BAC-19 — latent synthesis

True post-drift control value depends on a nonlinear latent that is not supplied as a candidate. The controller sees seven raw signals and generic pairwise primitives, then learns a one-dimensional latent by residual minimization.

Single-seed:
- synthesized-vs-true latent absolute correlation: `0.979`;
- old-space refit regret: `0.004628`;
- raw-linear expansion regret: `0.001061`;
- direct primitive expansion regret: `0.000668`;
- synthesized latent regret: `0.000129`;
- oracle latent regret: `0.000011`.

Eight-seed replication:
- birth: `8/8`;
- stationary false birth: `0/8`;
- mean latent correlation: `0.976`;
- mean direct primitive regret: `0.000719`;
- mean latent regret: `0.000157`;
- latent beat direct primitive in `8/8` seeds.

The synthesized feature is therefore doing more than adding another raw signal. It compresses a 28-dimensional primitive basis into a one-dimensional control coordinate.

## BAC-19c — sample efficiency

| Training samples | Latent regret | Primitive regret | Ratio |
|---:|---:|---:|---:|
| 5,000 | 0.000319 | 0.000907 | 0.351 |
| 9,000 | 0.000180 | 0.000682 | 0.264 |
| 16,000 | 0.000170 | 0.000632 | 0.268 |
| 28,000 | 0.000143 | 0.000583 | 0.245 |

Deployment model size:
- direct primitive: 168 action-model coefficients;
- latent representation: 60 action-model coefficients;
- global latent synthesizer: 32 parameters.

Decision: **PASS in the tested synthetic mechanism**.

Competing explanation: the primitive map already contains the algebraic ingredients needed to synthesize the true latent. BAC-21 must remove that assumption.

## BAC-20 — representation merge / retirement

Two representation members initially measure the same behavioral latent with mean correlation `0.975`.

Healthy redundant phase:
- keep-both regret: `0.0000584`;
- destructive average merge regret: `0.0000579`;
- one source only regret: `0.0000910`.

One source then changes semantics while the other remains valid.

| Policy | Accuracy | Regret |
|---|---:|---:|
| destructive merged feature, frozen | 57.60% | 0.003756 |
| keep both + refit | 90.09% | 0.000172 |
| logical merge + retire bad member | 90.15% | 0.000172 |

BAC-20b retirement control:
- degraded source retirement: `20/20`;
- stable-source false retirement: `0/20`.

Decision: destructive merge **FAIL** under constituent semantic drift. Provenance-preserving logical merge **PASS in the tested mechanism**.

The policy-level benefit over a full refit is small; the retained benefit is reversibility, state simplification, and the ability to isolate a changed constituent.

## New principles

1. `Representation birth != feature addition` — it can be causal compression.
2. `Representation merge != provenance deletion`.
3. `Representation accuracy != representation lifecycle health` — a representation can be accurate now but impossible to repair later if source lineage was destroyed.

## Updated architecture

```text
raw evidence sources
    -> primitive evidence map
    -> synthesized / born representation members
    -> logical equivalence groups
    -> active compact control state
    -> model / Prompt / organization allocator

member evidence and provenance remain addressable
    -> semantic drift detection
    -> member retirement / replacement
```

## Variable table

| Symbol | Meaning | Unit | Domain |
|---|---|---|---|
| `Psi(x)` | generic primitive map | none | vector |
| `w` | latent synthesis projection | none | real vector |
| `z_hat` | synthesized latent | none | [-1,1] |
| `G_r` | representation group | none | finite set |
| `R` | allocator regret | normalized utility | nonnegative |

Dimension check: the latent state is dimensionless in this benchmark. Regret and intervention value remain normalized utility, so comparison of downstream policy regret is dimensionally consistent.

## U
The next gate is primitive-map insufficiency. If the missing state is not recoverable from any current raw evidence, representation synthesis should stop and observation acquisition / sensor birth should become a candidate control action.

## ERROR CHECK

- Exact latent was not supplied, but required primitive ingredients were available.
- Nonconvex synthesis was replicated across seeds.
- Logical retirement did not materially beat full keep-both refit in regret; no larger claim is made.
- Hard safety is not delegated to representation synthesis, merge, or retirement.
# Bottleneck Allocator / Causal Evolution Track — 2026-08-28 v18

This file extends the retained BAC v17 ledger. All previous BAC-1..18 conclusions remain retained unless explicitly superseded below. All numerical findings are synthetic mechanism evidence; hard safety remains external.

## BAC-19 — latent feature synthesis

The exact correct structural feature was removed from the candidate dictionary. The controller received seven raw signals plus generic pairwise primitives and optimized a one-dimensional latent `z_hat = tanh(Psi(raw) @ w)` from residual evidence.

Retained results:
- single-seed latent-vs-true absolute correlation `0.979`;
- old-space refit regret `0.004628`;
- direct 28-dimensional primitive expansion regret `0.000668`;
- latent synthesis regret `0.000129`;
- oracle latent regret `0.000011`.

BAC-19b, eight-seed replication:
- representation birth `8/8`;
- stationary false birth `0/8`;
- mean latent-vs-true absolute correlation `0.976`;
- mean old-space regret `0.004765`;
- mean direct-primitive regret `0.000719`;
- mean latent regret `0.000157`;
- latent beat direct primitive expansion in `8/8` seeds.

New retained principle:

> Representation birth can be **causal compression**, not only feature addition.

## BAC-19c — sample efficiency / representation complexity

Latent synthesis beat direct primitive expansion in `5/5` replicates at every tested training size: 5k, 9k, 16k, 28k.

At 5k samples:
- latent regret `0.000319`;
- primitive regret `0.000907`.

At 28k:
- latent `0.000143`;
- primitive `0.000583`.

Deployment action-model complexity:
- direct primitive representation: `42` features/action, `168` action-model coefficients;
- latent representation: `15` features/action, `60` action-model coefficients;
- latent synthesizer: `32` global parameters.

## BAC-20 — representation merge / retirement

Two representation members initially measured the same behavioral latent with mean correlation `0.975`.

While semantics matched, keeping both and destructively averaging them had essentially equal regret (`0.0000584` vs `0.0000579`).

One source then inverted/degraded while the other remained valid.

Results:
- destructive merged representation, frozen: accuracy `57.60%`, regret `0.003756`;
- keep both + refit: accuracy `90.09%`, regret `0.000172`;
- logical merge with constituent provenance + retirement: accuracy `90.15%`, regret `0.000172`.

The important result is not a large welfare gain over a full refit. It is reversibility: destructive merge deleted the information needed to isolate the bad constituent.

New retained principle:

> Representation merge != provenance deletion.

BAC-20b retirement negative control:
- degraded member retired `20/20`;
- stable member false-retired `0/20`.

## Evolution hierarchy after BAC-20

1. Parameter evolution — Prompt patches, routing weights, transition parameters, verifier budget.
2. Dynamics-model population evolution — model birth, switch, specialization, retirement.
3. State-representation birth / latent synthesis — create new compact control coordinates.
4. Representation lifecycle — equivalence grouping, logical merge, member retirement, representation retirement.

Representation promotion and lifecycle operations require separate evidence gates and source provenance.

## Current next gates

1. BAC-21 primitive-map insufficiency / sensor birth: no function of current primitives can recover the missing state.
2. Observation acquisition as a control action competing with Prompt / Organization / Locator / Verifier by Future Control Value.
3. Correlated poisoning of representation-promotion evidence.
4. Joint model-birth + representation-birth controller.
5. Independent live/frozen Humies/LLM behavior gate while preserving the external hard runtime.

## ERROR CHECK

- The BAC-19 true latent was not supplied as a candidate, but its algebraic ingredients existed in the generic primitive map; arbitrary concept invention is not yet demonstrated.
- Latent synthesis is non-convex; multi-start optimization and replication are retained.
- BAC-20 retirement did not materially outperform a fully refit keep-both model; its retained value is state simplification and reversibility.
- Destructive merge is not universally harmful; it fails when constituent semantics later diverge.
- Hard runtime authority is unchanged.
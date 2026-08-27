# Experiment Progress — 2026-08-28 v18

New:
- BAC-19: correct structural feature removed from candidate dictionary; a one-dimensional latent was synthesized from generic raw primitives.
- BAC-19 v0.1 latent-vs-true absolute correlation `0.979`; old-space regret `0.004628`; latent regret `0.000129`; oracle latent `0.000011`.
- BAC-19b 8-seed replication: birth `8/8`, stationary false birth `0/8`, mean latent correlation `0.976`; latent beat 28-dimensional primitive expansion `8/8`.
- BAC-19c: at 5k/9k/16k/28k samples, latent representation beat direct primitive expansion in `5/5` replicates at every size. Deployment action-model coefficients: `60` vs `168`.
- New principle: `Representation birth can be causal compression, not only feature addition`.
- BAC-20: two redundant representation members were mergeable while semantics matched, but destructive merge failed after one member changed semantics.
- Destructive merged accuracy `57.60%`, regret `0.003756`; provenance-preserving logical retirement accuracy `90.15%`, regret `0.000172`.
- New principle: `Representation merge != provenance deletion`.
- BAC-20b: retirement gate detected `20/20` degraded sources and `0/20` stable sources.

Retained evolution hierarchy:
1. Prompt / policy / organization parameter evolution.
2. Dynamics-model population birth/switch/retirement.
3. State-representation birth / latent synthesis.
4. Representation-group merge/member retirement with provenance retained.

Next:
- BAC-21 primitive-map insufficiency / sensor birth: no function of current primitives can recover the missing state.
- Let observation acquisition compete with Prompt/Organization/Locator/Verifier interventions by Future Control Value.
- Correlated poisoning of representation-promotion evidence.
- Joint model-birth + representation-birth controller.
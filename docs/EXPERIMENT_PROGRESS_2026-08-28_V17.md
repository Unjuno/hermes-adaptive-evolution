# Experiment Progress — 2026-08-28 v17

New:
- BAC-17 structural misspecification: old feature-space refit regret 0.006869; representation birth 0.000021; oracle representation 0.000018.
- BAC-17b 12-seed replication: representation birth 12/12, correct structural-family first pick 12/12, stationary false birth 0/12.
- BAC-17c multiple-testing stress: naive in-sample scanner false-birth 20/20 for candidate pools 16, 64, and 256; independent heldout gate false-birth 0/20 while retaining 20/20 detection under structural drift.
- New principle: Residual search != structural evidence.
- BAC-18 telemetry poisoning: telemetry-authorized representation birth 12/12 false birth and poison-decoy selection 12/12; authoritative committed-effect holdout 0/12 false births.
- BAC-18 clean deployment: false representation reduced accuracy 91.37% -> 66.21% and regret 0.000117 -> 0.001877.
- New principle: Telemetry novelty != representation-birth authority.

Retained evolution layers:
1. Prompt / policy / organization parameters.
2. Dynamics-model population birth/switch/retirement.
3. State-representation birth/validation/retirement.

Representation promotion boundary:
discovery residual -> candidate feature -> independent heldout validation -> authoritative committed-effect confirmation -> provisional representation -> policy-value validation -> commit.

Next:
- BAC-19 latent-feature synthesis: construct a new latent representation rather than selecting a supplied candidate feature.
- BAC-20 representation lifecycle: merge/retire redundant born features.
- security: correlated poisoning of telemetry + pseudo-verifier evidence.
- integrate representation birth with model birth so a new representation can spawn a new dynamics-model family.

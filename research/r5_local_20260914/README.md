# R0/R4/R5 local closeout — 2026-09-14

This research branch records the local, non-production closeout after `research/r4-forced-mediation-20260911`.

## Retained results

- BAC-1..42 historical traceability: 28 hashed documents, no missing BAC number. Historical mechanisms remain `research_only` unless separately promoted by current evidence.
- R4 residual attack: UID separation did not hide `/proc` metadata; user namespace root retained mount capability until final capability drop; explicit resource limits and independent wall timeout were required; Landlock was unavailable in the tested kernel.
- Hardened reviewed-worker v0.2 uses a minimal root, empty `/proc`, closed inherited FDs, final capability drop, no-new-privileges, finite RLIMITs and an independent wall watchdog. This is a reviewed local fixture boundary, not a hostile-code sandbox proof.
- R5 fail-closed acceptance: 1000 unseen routing controls passed, with all unknown regimes returning NOOP and no execution authority.
- R5 crash/recovery: 200 reviewed local-state canaries converged to the declared old/new state across PREPARED/APPLIED/VERIFIED/normal positions.
- Regression suites: 640 passed in four non-overlapping completed groups.
- Release gate: v0.3 shadow-candidate metadata passes; canary/stable remain rejected because real-model paired value, real usage/cost and Hermes runtime validation are absent.

## Roadmap boundary

R0 historical/current local traceability is covered for the available BAC corpus. R2 is local-tested. R3 real calibration, R4 real Hermes canary and R5 canary/stable release remain open. R1 is the blocking external gate: an authorized real model/runtime, fixed paired task campaign and measured usage/cost are still required.

No operational branch merge, paid job, real-model inference, production deployment or execution authority is created by this branch.

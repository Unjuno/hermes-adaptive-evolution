# R5 local acceptance and R4 boundary hardening — 2026-09-12

## Scope

This work advances the retained R0–R5 roadmap only within the current local environment. No real LLM inference, paid job, production merge, model-facing execution tool, or continuing background job is created.

The previous R4 reviewed-worker mechanism was re-audited. Its network/user/mount namespace and FD controls were real, but the integrated launcher still exposed the host `/proc` view and did not bind CPU/process/file-descriptor/address-space/file-size limits. The reviewed canary recovery also overwrote an unrelated third state after a crash. Both issues were reproduced before repair.

## Process boundary result

A current-contract-like worker saw 16 host `/proc` PIDs including PID 1, had `no_new_privs=0`, NPROC=23715, NOFILE=16384, unlimited address space/CPU/file size, spawned all 20 finite child processes and opened 100 test FDs.

The hardened launcher adds fixed `no_new_privs`, NPROC/NOFILE/AS/CPU/FSIZE limits, a PID namespace, and masks `/proc` after recording namespace identity. In the finite control it saw zero `/proc` entries, could not address the known host parent PID, spawned only 6 of 20 children under NPROC=8, opened only 29 extra files under NOFILE=32, a busy loop was killed after about one second by a dedicated CPU-limit probe, and a 384 MiB allocation under a 256 MiB address-space probe returned `MemoryError`.

These are mechanism tests, not proof against kernel escape. The integrated fixed broker client uses more permissive fixed limits (NPROC 16, NOFILE 64, AS 512 MiB, CPU 5 s, FSIZE 8 MiB) and reports them back for validation.

## Canary recovery defect and fix

For PREPARED, APPLIED and VERIFIED crash journals, the old recovery code was given an unrelated `two_leaf` state before recovery. In all 3 cases it silently replaced that state with the old `solo` state.

The repaired recovery accepts only the exact declared before/after states. An unrelated state now raises a contract error without modification. The fresh follow-up preserved the third state in 3/3 cases.

Thus:

`Rollback authority != authority to overwrite unrelated concurrent state.`

## Historical evidence index

A machine-readable historical index now hashes the local BAC/runtime/prompt/evidence corpus. The first indexer incorrectly reported BAC-26/27 missing because it interpreted the filename `BAC25_BAC28...` as endpoints. The corrected index uses explicit Markdown BAC headings; BAC-1 through BAC-42 are all covered. File hashes establish consistency, not truth, and historical theory defaults to `research_only` unless promoted by the maturity manifest.

## R5 release gate

A release validator was added. A shadow-only candidate requires a passing maturity audit, clean test suites with zero failures/errors/skips, a verified rollback artifact, frozen source/corpus hashes, and zero execution-authority components. Canary/production modes cannot be promoted by this validator; they require the maturity manifest to already contain corresponding real-value evidence and no open external gates.

The local maturity manifest has 15 components and passes, with zero canary/production execution components. The actual local release audit accepted the non-executing shadow candidate and rejected both canary and production negative controls. Real-model value, real Hermes isolation, provider authentication and production release remain external/open gates.

## Validation

Completed non-overlapping regression groups after the fixes:

- core evidence/budget/broker/commit/R4/R5: 351 passed;
- environment/provider/producer: 176 passed;
- shadow CLI/router/ledger: 117 passed.

Total: 644 passed, zero failures/errors/skips in the completed groups.

A runtime package apply/rollback roundtrip restored the exact pre-R5 runtime tree SHA-256. The portable local reproducer also passes with `/proc` masked, `no_new_privs=1`, process-cap enforcement and concurrent-canary-state preservation.

## Boundary

R0 local corpus indexing and the local shadow-release acceptance mechanism are now closed for the available artifacts. R4/R5 local reviewed mechanisms are closed as fixtures only. R1 real-model paired value, R3 real-task calibration, R4 real-Hermes containment and R5 production acceptance remain blocked by external/runtime evidence; synthetic evidence is not substituted for those gates.

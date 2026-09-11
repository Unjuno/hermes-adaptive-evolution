# R4/R5 local hardening and release-readiness — 2026-09-12

## Scope

This branch records a local R4/R5 mechanism slice. It does **not** contain real Hermes/LLM value evidence, does not start a paid job, does not merge the operational plugin, and does not grant execution authority. The complete cumulative runtime and tests are delivered separately in the conversation package; this branch keeps a portable reproducer and compact research status.

## Finding 1 — UID + mount/net namespace was still too weak

The previous reviewed launcher used a separate host UID and new user/mount/network namespaces while retaining most of the host filesystem. A reviewed negative control reproduced all of the following:

- a host file owned by the worker UID was changed;
- a separate host process with the same UID accepted SIGTERM and exited;
- parent/root process command-line metadata was readable through `/proc`;
- RLIMIT_AS, RLIMIT_CPU and RLIMIT_FSIZE were unlimited.

The earlier network result remained true: a new direct provider connection was blocked. The failure was therefore in filesystem/process/resource authority, not in the network-namespace observation.

Retained principle: **separate identity is insufficient if that identity still has ambient host state/process authority or unbounded resources.**

## Finding 2 — reviewed minimal-root/PID/resource launcher

A new local mechanism adds:

- distinct host UID/GID;
- user, mount, network and PID namespaces;
- fixed client as PID 1 in the new PID namespace;
- no `/proc` inside the jail;
- minimal root containing the reviewed Python runtime plus a read-only broker IPC bind;
- `close_fds=True` and no inherited extra descriptors;
- cleared bounding/inheritable/ambient capabilities plus `no_new_privs`;
- finite RLIMIT_NPROC/NOFILE/AS/CPU/FSIZE/CORE;
- rejection of worker-writable path ancestors.

Actual reviewed broker execution passed. An inheritable file FD and connected TCP FD were intentionally left open in the operator; the worker reported zero extra FDs, the host file stayed unchanged, a same-UID host process survived, and exactly one provider POST occurred through the broker.

This remains a fixed reviewed-client mechanism, **not** a general arbitrary-code/kernel sandbox.

## Finding 3 — resource limits were exercised

In the minimal-root/PID-namespace structure:

| Stress | Result |
|---|---|
| allocate 600 MiB with 512 MiB address-space cap | `MemoryError` |
| open descriptors with NOFILE=64 | failed after 61 sockets |
| fork 100 children with NPROC=32 | failed after 30 children |
| infinite loop with CPU=1 s | killed after about 1.02 s |

Exact usable counts are environment-specific. The claim is only that the configured limits actually stopped the reviewed stress cases.

## Finding 4 — runtime metadata was not runtime identity

The first hardened version hashed only runtime metadata. A root-owned stdlib file was modified while safe ownership/mode were preserved:

- the file SHA changed;
- the runtime metadata contract hash did not change;
- validation accepted the modified tree.

The fix binds the contract to a deterministic digest over **1,417 runtime entries** (path/type/mode plus size/SHA-256 for files). Schema is now `adaptive-evolution.reviewed-worker-runtime.v0.2`. The fresh follow-up rejects the same modification with `runtime content digest differs`.

Retained principle: **runtime identity != runtime metadata identity.**

## Finding 5 — maturity labels are not release authority

An R5 typed-evidence release gate was added above the existing maturity manifest. Current state:

- 16 maturity components;
- maturity audit PASS;
- execution components `[]`;
- current value evidence remains synthetic/local;
- candidate release audit **BLOCKED** with 21 explicit blockers.

Negative control: target maturity labels were edited to `release_validated` and blockers cleared. The ordinary maturity audit passed, but the release gate still blocked because real runtime identity, real shadow value, real usage cost, real canary and unseen-task holdout evidence kinds were absent.

Retained principle: **status self-report != release authority.**

Typed evidence and hashes still do not prove causal truth or independent human review; they only make a status-label edit insufficient.

## Validation

Final cumulative tree: **639 tests passed** in three non-overlapping completed groups: `231 + 204 + 204`.

Fresh R5 application to the reconstructed pre-R5 cumulative tree added four files. Reapplication changed zero files. The fresh-applied tree passed the same three groups (`639` total). A deliberately modified new file caused `REFUSE_UNKNOWN_EDIT` rather than overwrite.

A later single full-suite command was attempted only to generate a unified JUnit file, but the tool execution limit interrupted it at 67%. That incomplete run is **not** claimed as a pass; the completed non-overlapping groups are the validation basis.

## Roadmap boundary

- R0: current local subset content-bound/reproducible; historical/operational integration remains open.
- R1: real model/task/value/cost evidence remains the main external blocker.
- R2: local shadow/provider/budget/broker path remains tested.
- R3: synthetic/local commit mechanism is tested; real-task calibration remains open.
- R4: reviewed local forced mediation is strengthened; real Hermes image/kernel review and semantic side effects remain open.
- R5: mechanical release gate exists and correctly BLOCKS the current state; production release remains open.

## Reproduce

After applying the separately delivered R5 package to the cumulative payload:

```bash
python research/r5_local_hardening_20260912/reproduce_r5_local.py \
  --payload /path/to/cumulative/payload \
  --output /tmp/r5-local-control.json
```

The reproducer performs no model/provider/billing call. It checks runtime-content drift rejection, the reviewed minimal-root fixed client, and a label-only release-evidence negative control.

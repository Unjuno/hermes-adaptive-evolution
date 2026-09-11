# R4 local forced mediation and reviewed reversible canary — 2026-09-11

## Scope

R0–R5 remain the long-term roadmap. This branch records a bounded R4 local mechanism study; it does **not** claim real Hermes/LLM canary authority or production release. Provider behavior in the study is a reviewed loopback HTTP stub. No model download, paid inference, operational merge, or learned execution authority was used.

The complete cumulative implementation and 627-test delivery are distributed separately as a conversation artifact. This branch intentionally contains a portable reproducer and research record rather than pretending the operational branch already contains all cumulative runtime dependencies.

## Finding 1 — separate UID + network namespace can force reviewed traffic through the broker

The operator/broker ran as the host operator UID while the reviewed worker ran as host UID/GID 65534 inside a new user+mount+network namespace. In the reviewed control:

- an unisolated UID-65534 process could reach the parent loopback provider;
- the isolated worker could not reach that provider directly even after bringing up its own loopback;
- the operator-owned authority DB could not be read or written;
- a root-only decoy Unix socket could not be connected;
- joining the parent network namespace with `setns` was denied;
- the worker-owned broker Unix socket succeeded and produced exactly one generation POST.

This is a finite reviewed-worker control, not a hostile-code sandbox proof.

## Finding 2 — namespace isolation does not revoke inherited capabilities

A stronger negative control intentionally inherited resources opened **before** isolation:

- a root-opened writable file descriptor remained writable after the host UID was dropped;
- a TCP socket connected in the parent network namespace remained usable inside the new network namespace;
- newly created TCP sockets were still blocked.

Therefore:

> Namespace isolation != inherited capability revocation.

The fixed launcher consequently uses `close_fds=True`, a minimal environment, a separate host UID and new user/mount/network namespaces. With dangerous parent FDs deliberately marked inheritable, the reviewed child started with no descriptors above stdio, the operator file remained unchanged, and the broker still produced one generation request.

## Finding 3 — network namespace != filesystem IPC isolation

A world-accessible filesystem Unix socket used as an ambient proxy remained reachable from a new network namespace. Thus the network namespace alone does not remove every local IPC path.

A follow-up minimal-root/chroot control bind-mounted only the broker IPC directory. In that environment:

- the ambient Unix proxy path was absent;
- the authority DB path was absent;
- direct parent HTTP was unavailable;
- `/broker/broker.sock` succeeded;
- provider generation count was one.

This is evidence for a minimal reviewed client. A complete Hermes runtime image, dependencies, tools, and arbitrary generated programs remain a separate containment gate.

## Finding 4 — reviewed local-state canary recovery

A new fixture-only canary executor is restricted to the declared action class:

`local_state_only_no_external_effects`

It accepts no arbitrary path, command, provider request, model change, prompt patch, or tool execution. The plan freezes an approval capability hash, `from_state`, `to_state`, and expiry. Backup+journal writes are fsynced and the state replace is atomic.

Crash injection produced:

| crash point | recovery | final state |
|---|---|---|
| after PREPARED | ROLLED_BACK | old |
| after local apply | ROLLED_BACK | old |
| after durable verification | COMMITTED | new |

A normal execution committed once; replay produced no second mutation. Twelve concurrent processes yielded one COMMITTED and eleven REPLAY_NO_CHANGE outcomes.

## Finding 5 — state rollback is not semantic effect rollback

A negative control performed a local canary state change and an external HTTP side effect, then forced verifier failure and restored the local state. The local state returned to its original value, while the external side-effect count remained one.

Therefore:

> State rollback != semantic effect rollback.

The reviewed executor now refuses external-effect action classes. Real Hermes actions involving emails, payments, remote writes, tool calls, or other external effects require independently validated idempotency/compensation/transaction semantics before canary authority.

## Implementation and validation

New local modules in the delivered package:

- `forced_mediation.py`: separate-worker-UID broker service plus fixed isolated broker client launcher; explicit FD hygiene; no learned execution authority.
- `reviewed_canary.py`: local-state-only reversible fixture canary with approval, precondition, crash recovery and replay idempotency.

Non-overlapping final pytest groups:

- 271 passed — broker/evidence/commit/R4 controls;
- 117 passed — shadow CLI/router/ledger;
- 239 passed — environment/provider/producer/task protocol;
- **627 passed total**.

The R4 package was then applied to a fresh cumulative pre-R4 tree: 21 files changed on first application, zero on reapplication; the portable reproducer passed; the same 627 tests passed; an unknown edit was refused and preserved.

The maturity manifest now contains 14 components and passes validation. `execution_components=[]`. `forced-mediation-reviewed-worker` and `reviewed-reversible-canary` remain synthetic-only with no runtime authority.

## Roadmap boundary

- R0: current delivered subset reproducible; historical full-corpus integration remains open.
- R1: real paired model/task value and real monetary/token costs remain open. No local model/cache was found and no external spending cap/model campaign was registered.
- R2: local shadow/provider/budget/broker chain tested.
- R3: synthetic/local commit mechanism closed; real-task calibration open.
- R4: **local reviewed mechanism CLOSED_FIXTURE**; real Hermes containment and value-backed canary OPEN.
- R5: release acceptance open.

The next valid gate is real-model shadow evaluation under a separately fixed model revision, task set, metric, provider usage accounting, and monetary spending cap. Passing these R4 mechanism controls alone must not authorize a real agent change.

## Reproduce

After obtaining the separately delivered cumulative R4 implementation payload, on a Linux environment with user namespaces and the required operator privileges:

```bash
python research/r4_forced_mediation_20260911/reproduce_r4_local.py \
  --payload /path/to/cumulative/payload \
  --output /tmp/r4-local.json
```

The reproducer uses a reviewed local HTTP stub and a local JSON fixture. It does not call a real model or billing service.

## Limits

The user-namespace/kernel boundary is not itself a proof against kernel escape. The minimal chroot experiment is not a general-purpose generated-code sandbox. Local capability hashes are consistency controls, not production key management. Provider identity, actual Hermes subprocess/tool behavior, real task value, semantic compensation, and real costs remain unresolved.

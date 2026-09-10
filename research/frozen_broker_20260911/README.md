# R1/R2: frozen-operation broker and caller-disconnect recovery — 2026-09-11

## Scope

The R0–R5 roadmap is retained. This slice completes local request/authority API separation, not real Hermes inference or production release. Previous 530 delivered tests were reproduced. A cumulative conversation package adds request_broker.py, a finite Unix-domain-socket service and a scoped client interface above CampaignBudget.

All provider requests went to reviewed loopback HTTP stubs with scripted outputs and usage counts. No real LLM, model download, paid job, explicit workflow dispatch, operational merge or learned execution authorization was used. The three integer-extraction cases are one finite fixture family, not independent population performance evidence.

This branch contains a small actual-HTTP API reproducer and this report. It requires --payload pointing to the separately delivered cumulative implementation. The full implementation, HTTP/Unix-socket studies, 598 tests, before-fix regressions, receipts, proof, updated roadmap and guarded application script are in the conversation package. They are not implicitly merged into the operational plugin.

## Fixed operator and worker interfaces

The operator freezes campaign/run plans, client credential hashes and allowed runs, a bounded validity window and the authority DB. A worker request contains exactly schema, broker_hash, client_id, credential and operation_id. It cannot supply a DB path, a new campaign, provider endpoint, prompt body, token reservation or settlement. The broker constructs the registered request, independently scores the response and settles its own ledger.

The service uses AF_UNIX, private same-UID socket permissions and scoped random bearer capabilities. These are application controls, NOT a sandbox against hostile same-UID code. DB owners and clients with direct provider network access remain outside this guarantee. The request catalog limits permitted operations but does not itself enforce statistical enrollment order.

## Actual HTTP and IPC controls

| Condition | Generation POSTs | Known scripted tokens | Unresolved reservation |
|---|---:|---:|---:|
| Normal | 2 | 30 | 0 |
| Wrong answer | 2 | 30 | 0 |
| Missing usage | 1 | 0 | 100 |
| Nonterminal response | 1 | 0 | 100 |
| Reported 210 against reservation 100 | 1 | 210 | 0 |
| Lost provider reply | 1 | 0 | 100 |

Further requests from another registered run were blocked by the shared cap or unresolved state. Known zero is not a claim that unknown consumption is zero. The 210 report was retained, not clipped to the reservation.

Five unauthorized/malformed attempts (invalid capability, another client's run, DB replacement, false settlement and payload injection) all returned DENIED, with zero provider GETs, zero POSTs and zero reservations.

Twelve concurrent IPC callers submitting the same operation produced one ADMITTED and eleven REPLAY_NO_SEND responses, one provider POST and the same receipt hash. This is a concurrency control, not a throughput benchmark.

## Follow-up: caller failure differs from broker failure

A caller sent a complete IPC frame and disconnected without reading the result. The separate broker completed generation and durable settlement. Reconnecting with the same operation returned REPLAY_NO_SEND plus the saved success receipt; provider POST count stayed one.

Broker crash remains ambiguous. Using the same frozen plan/endpoint, one broker process exited after reservation but before send; another after the response but before settlement. Server POST counts were zero and one, but recovered campaign snapshots were identical. Both restarts refused resend and returned no settled receipt. Moving the boundary improves caller-disconnect recovery but does not solve remote exactly-once execution or reconciliation.

## New defects reproduced before repair

1. The initial broker could dispatch generation after its validity window expired during the version/tags preflight. A regression first failed, then a second check immediately before dispatch prevented that POST. This is a local clock check, not hard real-time cancellation or protection against clock rollback.
2. The initial client checked broker_hash but could accept a different operation ID, a mismatched receipt request ID, execution_authorized=true, an unknown disposition, or a mutated receipt body. Five regressions first failed. The client now checks operation binding, exact schemas, non-authority, disposition and a digest of the transported receipt projection.

Six initially failing cases and the initial source were saved. These were defects in the NEW extension, not in a previously released broker. Receipt hashes are consistency checks, not authenticated provider signatures.

## Boundary negative control

After two broker-approved requests exhausted the cap, a reviewed test client directly called the provider once. The provider saw three POSTs while the broker ledger had two requests. No network enforcement was installed. Thus the broker cannot enforce an administrator's lifetime budget, prevent same-UID database replacement, or block direct HTTP outside this API. Separate OS identity/containment and enforced routing remain R4 prerequisites.

## Validation

Baseline: 530 passed. Added: 68. Revised implementation: 598 passed, no failures/errors/skips. Fresh cumulative application: the same 598 passed in one command. This is the delivered subset, not the complete upstream/Hermes end-to-end suite.

All 68 applied payload hashes matched. Previous-package upgrade added six files; repeat application changed zero. Unknown local edits were refused and preserved. The complete HTTP/Unix-socket study was rerun on applied code and its outcome/count/budget/recovery summaries matched. The smaller repository reproducer also ran on applied code.

The research runner additionally reconstructs TaskProtocol events with a synthetic logical replay clock. This validates offline reconstruction, NOT live-model task deadlines or independent task populations.

Environment: Python 3.13.5, SQLite local filesystem, Linux, AMD EPYC 9V74. CPU clock not pinned. No model/GPU/token-price/throughput claim. Servers and subprocesses were stopped; no continuing job was installed.

## Real-model path and long-term roadmap

Local checks still found no Hermes/Ollama/container runtime/model cache and failed DNS resolution. However, the connected Hugging Face authentication and Jobs-list reads succeeded; existing Jobs count was zero. An external execution capability therefore exists in principle. New Jobs are usage-billed and no spending limit or selected model revision was registered for this slice, so no job was started. Do not confuse a local token-admission cap with a cloud monetary spending cap.

R0 remains open for historical corpus/operational integration. R1 needs actual model results and real costs. R2 has a local narrow broker, but Hermes-specific state/tool/runtime validation remains open. R3 adaptive operational commit, R4 forced mediation/reversible canary and R5 release acceptance are not complete. Local M0–M4 completion does not rename those external gates as PASS.

## Reproduce

After obtaining the cumulative conversation package, Python 3.11+ and a new output path:

```bash
python research/frozen_broker_20260911/reproduce_broker_scope.py \
  --payload /path/to/unpacked-package/payload --output /tmp/new-broker-control.json
```

The short reproducer checks actual HTTP plus direct broker API scope/caps/replay, not the full separate-process UDS study. Fixed test credentials in it are not deployment secrets. No model or billing service is called.

## Primary implementation references

- https://www.sqlite.org/lang_transaction.html
- https://docs.python.org/3/library/socket.html
- https://docs.python.org/3/library/hmac.html
- https://huggingface.co/docs/hub/en/jobs-pricing

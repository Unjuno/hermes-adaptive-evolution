# R1/R2: fixed cross-run campaign budget and recovery — 2026-09-11

## Scope

R0–R5 remain the long-term roadmap. This slice closes local shared-admission preparation, not real Hermes/LLM evaluation or production release. Previous 470 delivered tests were reproduced. The cumulative conversation package adds a frozen multi-run CampaignBudget, opt-in local_text_pair integration, immutable historical snapshots and a separate audit-projection DB type.

Only reviewed loopback HTTP stubs were contacted. Responses and usage counts are scripted, not model inference, authenticated token metering or monetary cost measurements. No model download, paid provider, explicit workflow dispatch, operational merge or learned execution authority was used.

This research branch contains the reproducer and this report. The reproducer requires --payload pointing to the delivered cumulative implementation (or a directory to which it was applied). It intentionally does not pretend the previous operational branch already contains the new runtime dependencies. The complete runtime, 530 tests, before-fix regressions, wire receipts, proof and guarded application script are distributed in the conversation package.

## Primary comparison

Two registered runs each permit two generation requests.

| Condition | Separate per-run ledgers | Shared campaign |
|---|---:|---:|
| Completed responses, intended cross-run cap two | 4 POSTs total | 2 POSTs total |
| Lost reply, then move to another run | 2 POSTs total | 1 POST; next run sends none |

The old implementation did not violate its declared per-run guarantee. The experiment exposes a previously explicit scope limitation. The shared implementation freezes the run registry and plan hashes, checks per-run and campaign caps in one write transaction, and never creates an unseen run implicitly.

## Final actual HTTP controls

| Mode | POSTs | Run B POSTs | Known scripted token count | Unresolved reservation |
|---|---:|---:|---:|---:|
| Normal | 2 | 0 | 30 | 0 |
| Wrong answer | 2 | 0 | 30 | 0 |
| Lost reply | 1 | 0 | 0 | 100 |
| done=false | 1 | 0 | 0 | 100 |
| Missing final usage | 1 | 0 | 0 | 100 |
| Output overrun | 1 | 0 | 210 | 0 |
| Model mismatch | 1 | 0 | 15 | 0 |

Wrong answers still consume reported resources. Missing usage is not zero consumption. Faults with known usage can still halt the campaign. In the overrun condition the campaign token cap was 150 and the request reservation 100, but the server reported 210. The ledger retained 210 and blocked new admissions; it did NOT enforce the remote token cap or undo the overrun. The generated task records and both run reports passed offline audit in each cell.

The integer-extraction cases are a single finite template family, not independent population-level evidence.

## Recovery and concurrency follow-ups

Two worlds used exactly the same frozen plan, endpoint and payload. In world 0 a subprocess exited after reservation commit but before send; in world 1 it exited after receiving a successful response but before settlement commit. Server operation counts were 0 and 1. The complete recovered campaign snapshots were identical. Both new-run admissions were refused.

This avoids automatic duplicate work but strands an unsent operation in world 0. No lease-expiry refund, automatic reconciliation or exactly-once claim is made. Provider-side idempotency, cancellation or authenticated result lookup would be additional assumptions/interfaces, not capabilities implemented here.

Twenty-four independent subprocesses racing for admission produced one ADMITTED and 23 BLOCKED_CAMPAIGN_UNRESOLVED. This strict implementation serializes in-flight work even when it is benign. That is an availability/parallelism cost, not a throughput advantage.

A negative control intentionally created a new DB with the same plan after the original DB was blocked. The new DB admitted a request. Thus this mechanism only enforces a fixed shared ledger for participating clients; it cannot enforce an administrator's lifetime budget or prevent direct HTTP calls outside the client.

## Defects found in the new extension before repair

1. The initial audit projection used the same database application ID as ProviderBudget. It could be reopened as a fresh per-run admission authority, bypassing the intended shared budget scope. One regression failed before the fix. The projection now has a distinct application ID; the old admission API rejects it and audit checks the declared DB role.
2. The new settle API accepted contradictions between the explicit final token count and receipt usage, including mismatched sums, missing usage and boolean counters. Five regression cases failed before repair. Such contradictions now fail before mutation, retaining the original unresolved reservation.

These were defects in the initial NEW extension, not claims that the previous 470-test release already contained CampaignBudget. Failing logs and before-fix source snapshots are retained. Shape/consistency validation is not provider authentication.

## Implementation contract

- A campaign is explicitly initialized once with finite registered run IDs, immutable plan hashes, per-run limits and shared limits.
- Both shared and per-run limits are checked in one SQLite BEGIN IMMEDIATE transaction. There is no dual-ledger accounting commit.
- Identical request-ID replays return REPLAY_NO_SEND. Conflicting run, payload or reservation is rejected.
- IN_FLIGHT, UNKNOWN, OVER_LIMIT or an explicit provider fault blocks subsequent requests across registered runs.
- Existing unknown receipts cannot be rewritten into a zero-cost success/refund.
- Each run exports a consistent historical campaign snapshot and a differently typed audit projection. Neither is a current admission authority. A past run remains auditable after a later run changes the shared ledger.
- Campaign mode is explicit via --campaign-plan and --campaign-db. Legacy mode remains per-run only; omitting campaign mode does not magically retain a total budget.
- Input token reservations remain declarations, not proven tokenizer or billing bounds. No result authorizes autonomous execution.

## Validation

Baseline: 470 passed. New cases: 60. Final implementation: 530 passed, zero failures/errors/skips. Fresh cumulative application: the same 530 passed in one command. This is the delivered subset, NOT the complete upstream/Hermes end-to-end suite.

All 62 applied payload hashes matched. Previous-package upgrade changed 9 files; repeat application changed 0. An unknown local edit was refused and preserved. The applied CLI initialized the campaign, ran A and B, and audited both without extra POSTs: A generated twice, B zero times, known scripted usage 30. The implementation-bound no-network reproducer separately confirmed 4 vs 2 admissions, 2 vs 1 after an unknown request, and projection-role refusal.

Environment: Python 3.13.5, SQLite 3.46.1, Linux, AMD EPYC 9V74, local filesystem; CPU clock not pinned. No model/GPU/throughput or real-money benchmark. A private venv avoided unrelated system startup hooks. Tests were not skipped.

## Roadmap boundary

Local M0–M4 (reproduce, cross-run control, implement, follow up faults, apply/retest) are complete. Historical corpus integration, authorized real-model comparison, Hermes-specific tools/memory/runtime validation, adaptive operational commit, reversible canary and release remain open. No continuing job is installed. Local readiness checks still found no hermes, ollama, docker, podman or bwrap executable; this is not a claim that every external service is unavailable.

## Reproduce

After obtaining the separately delivered cumulative package, Python 3.11+:

```bash
python research/campaign_budget_20260911/reproduce_campaign_admission.py \
  --payload /path/to/unpacked-package/payload --output /tmp/new-budget-control.json
```

The reproducer does not send network requests. Full actual-HTTP, crash and concurrency study receipts and runners are in the cumulative artifact. Use a new output path.

For configured, explicitly authorized local evaluation, initialize once and pass the same shared DB to both runs. The included examples use placeholders and are not model recommendations. Offline audits read the saved historical snapshot, not a live authoritative budget.

## Primary implementation references

- https://www.sqlite.org/lang_transaction.html
- https://docs.python.org/3/library/sqlite3.html
- https://docs.ollama.com/api/usage

The guarantee is about participating client admission under fixed ledger and truthful bounded settlement assumptions. It does not authenticate external execution, prevent DB-owner bypass, or recover unknowable remote outcomes.

# R1/R2: text-provider bridge and ambiguous request accounting — 2026-09-10

## Scope and roadmap

R0–R5 remain the long-term gates. This work closes connection preparation, not real Hermes evaluation or production deployment. Previous 401 delivered tests were reproduced. A cumulative conversation package adds a text-only Ollama-native protocol bridge and a durable per-run request admission ledger. No Hermes SDK, actual LLM, model download, paid provider, workflow dispatch, operational merge, or learned execution authorization was used.

Actual HTTP requests were sent to a finite reviewed loopback stub. Responses and token fields are scripted. These are transport/measurement controls, NOT model-quality or real token/currency measurements. The three integer-extraction cases belong to ONE fixture template family. Repetitions and the three different integers do not establish independent task populations.

This research branch contains the standalone lost-reply reproducer and this report. Complete new modules, cumulative R2 dependencies, 470 tests, full wire study, receipts, plans, proof and guarded apply script are in the conversation package. The operational plugin is not implicitly updated by this branch.

## Local milestones

M0 reproduced 401 tests and checked availability. M1 implemented an opt-in numeric-loopback text client and durable request accounting. M2 exercised actual HTTP against reviewed response faults. M3 followed lost replies into duplicate work and process-crash ambiguity, and fixed two defects using initially failing regressions. M4 completed 470 tests before and after fresh application, previous-package upgrade, idempotency, 54 payload hashes, unknown-edit refusal and applied CLI run/audit.

These are R0/R2 contributions. Real model value and R3–R5 remain open.

## Wire study

Three fixed cases, four planned attempts per case per arm: 24 scheduled calls per cell. Skipped calls remain registered and unknown, not converted to successes.

| Condition | POSTs | Known successes | Known failures | Unknown returned results |
|---|---:|---:|---:|---:|
| Correct reviewed response | 24 | 24 | 0 | 0 |
| Incorrect integer | 24 | 0 | 24 | 0 |
| Self-report SUCCESS, not required JSON | 24 | 0 | 24 | 0 |
| Correct-looking JSON, length termination | 24 | 0 | 24 | 0 |
| Nonterminal done=false | 1 | 0 | 0 | 1 |
| Correct output, missing usage | 1 | 1 | 0 | 0 |
| Unexpected model name | 1 | 0 | 0 | 1 |
| Model digest changes after generation | 1 | 0 | 0 | 1 |
| Correct output, output-token violation | 1 | 1 | 0 | 0 |
| HTTP error | 1 | 0 | 0 | 1 |
| Lost reply after processing | 1 | 0 | 0 | 1 |
| Registered call cap of two | 2 | 2 | 0 | 0 |

Success was fixed before running: normal terminal completion plus strict JSON containing exactly one integer value matching the local reference. A length-terminated answer is zero for THIS endpoint, not a universal claim that truncated artifacts lack value.

Task outcome and final usage are separate. Missing usage is not zero cost. Nonterminal counters remain unfinalized. A failed answer can still consume reported resources. No returned text is executed.

## Follow-up: timeout is not non-execution

The stub records an operation before delaying its reply beyond the client timeout. One request produces one server operation and a client TimeoutError. Three naive retries of the same payload produce three operations and three client TimeoutErrors. Identical payload hashes do not create server idempotency.

The new ledger reserves before send and returns REPLAY_NO_SEND on repeated request IDs. It neither cancels nor recovers the remote operation.

An actual subprocess crash follow-up used os._exit after reservation. One world exited before send; the other after receiving the response but before durable settlement. Server operation counts were 0 and 1; recovered local IN_FLIGHT records were identical. Both restarts refused resend. This sacrifices availability in the unsent world, not an exactly-once solution. The finite indistinguishability proof is included in the package.

## Defects reproduced before repair

1. Early return for length termination skipped an output-token violation check.
2. Nonterminal done=false counters could be settled as final usage.

Both failed regression cases on the initial new bridge were retained before fixes. Scoring and metering now run independently; nonterminal usage remains unresolved. Initial exploratory wire results are not the adopted result; final results are tied to revised implementation hashes.

## Implementation boundaries

- `python -m adaptive_evolution_observer.local_text_pair --plan PLAN.json` validates without network.
- `--run-local --output NEW_RUN_DIRECTORY` explicitly performs local evaluation.
- `--audit --output RUN_DIRECTORY` replays receipts offline.
- Numeric IPv4 loopback only; no proxy inheritance, redirects, retries, model pulls, arbitrary tools or generated code execution.
- GET version/tags before and after POST: server declarations, not authenticated atomic model snapshots. Change-and-change-back is not excluded.
- SQLite binds request IDs, payload hashes, reservations and settlement. Unknown/in-flight/over-limit requests halt new admissions. Existing run directories are never silently re-executed.
- Input reservations are declared, not proven tokenizer bounds. Client admission limits are not a guarantee against false server billing.
- Socket timeouts do not mean cancellation, strict wall isolation or a global cross-run budget.
- `population_promotion_eligible=false`; statistical output never grants execution authority here.

## Validation

Baseline 401 passed. New cases 69. Final implementation 470 passed. Fresh applied package 470 passed. No failures/errors/skips in these completed suites. This is the delivered subset, NOT the entire upstream/Hermes test suite.

All 54 payload hashes matched. Upgrade added five files; reapplication changed zero. Unknown edits were refused and preserved. Applied CLI completed six reviewed requests, offline audit reproduced evidence, and repeated inference into that directory was refused without extra requests.

Python 3.13.5, Linux, SQLite/local filesystem. CPU clock not pinned. No throughput claim. Stub token fields are not real LLM token measurements.

## Next gate

An authorized installed model or independently isolated Hermes runtime is required for real evaluation. Local checks found no Hermes/Ollama/container sandbox/model cache and external DNS was unavailable. A connector search did not yield a verified runtime for this slice; this is not a claim that every external service is unavailable.

Begin with text-only paired tasks and fixed model/version/prompt policies plus real usage receipts. Then validate the specific Hermes wrapper's tool permissions, state and full-run usage. Do not substitute this stub for that gate. No continuing job is installed.

## Reproduce

Python 3.11+, standard library, fresh output path:

```bash
python research/provider_transport_20260910/reproduce_lost_reply.py --output /tmp/lost-reply-example.json
```

A temporary numeric-loopback server runs reviewed fixed behavior and is shut down afterward. Fetched Git blob SHA matched the locally executed source.

## Primary interface references

- https://docs.ollama.com/api/generate
- https://docs.ollama.com/api/usage
- https://docs.ollama.com/api/tags
- https://docs.python.org/3/library/http.client.html
- https://hermes-agent.nousresearch.com/docs/guides/python-library

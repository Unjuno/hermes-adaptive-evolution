# R1/R2: bounded text-provider bridge and ambiguous request accounting — 2026-09-10

## Scope

The long-term R0–R5 roadmap is retained. This work closes a local connection-preparation slice, not real Hermes evaluation or production deployment. Previous 401 delivered tests were reproduced. A cumulative conversation package adds a text-only Ollama-native protocol bridge and a durable per-run request admission ledger. No Hermes SDK, actual LLM, model download, paid provider, workflow dispatch, operational merge, or learned execution authorization was used.

Actual HTTP requests were sent to a finite reviewed loopback stub. Its responses and token fields are deliberately scripted. These are transport/measurement fault controls, NOT model-quality measurements or real token/currency costs. The three fixture families and their repeated attempts do not support population inference.

This research branch contains the standalone standard-library lost-reply reproducer and this report. The complete new modules, cumulative previous R2 dependencies, 470 tests, full wire study, exact input/output receipts, plans, proof and guarded application script are in the conversation package. They are not implicitly integrated into an operational plugin by this branch.

## Local milestones

- M0: inspected previous roadmap/package, reproduced 401 tests, checked backend availability.
- M1: implemented opt-in numeric-loopback text-only client; explicit provider version/model digest checks; frozen prompts, task registry, attempt counts and local scorer; durable request reservations.
- M2: exercised real HTTP transport against reviewed correct/wrong/truncated/incomplete/missing-usage/model-drift/lost-reply faults.
- M3: followed a lost reply into duplicate work and process-crash ambiguity; found and fixed two defects in the new bridge with initially failing regressions.
- M4: 470 tests passed on implementation and again after fresh cumulative application; previous-package upgrade, unchanged reapplication, 54 payload hashes, unknown-edit refusal and applied CLI run/audit passed.

These milestones contribute to R0/R2. R1 real model value and R3–R5 remain open.

## Wire study

Three fixed text fixtures, four planned attempts per fixture per arm: 24 scheduled calls per cell. Faults stop subsequent admission as shown; skipped calls are not converted to successes or removed from the registry.

| Condition | Actual POSTs | Known successful outputs | Known failed outputs | Unknown returned outputs |
|---|---:|---:|---:|---:|
| Correct reviewed response | 24 | 24 | 0 | 0 |
| Incorrect integer | 24 | 0 | 24 | 0 |
| Self-report SUCCESS, not required JSON | 24 | 0 | 24 | 0 |
| Correct-looking JSON but length termination | 24 | 0 | 24 | 0 |
| Nonterminal done=false | 1 | 0 | 0 | 1 |
| Complete correct output, missing usage | 1 | 1 | 0 | 0 |
| Unexpected model name | 1 | 0 | 0 | 1 |
| Model digest changes after generation | 1 | 0 | 0 | 1 |
| Correct output but output-token violation | 1 | 1 | 0 | 0 |
| HTTP error | 1 | 0 | 0 | 1 |
| Lost reply after stub processing | 1 | 0 | 0 | 1 |
| Registered call cap of two | 2 | 2 | 0 | 0 |

Success was fixed before running: strict JSON containing exactly one integer `value`, matching the independent local reference, and normal terminal completion. A length-terminated correct-looking answer is score zero for THIS endpoint, not a universal statement that truncated artifacts have no value.

Task score and usage completeness are separate. Missing final usage is not zero cost. Nonterminal counters are retained as unfinalized rather than settled usage. A known failure can still consume measured/reported resources. The runner never executes returned text.

## Follow-up: timeout is not evidence of non-execution

The stub increments its processed-work counter before delaying the reply beyond the client timeout.

- One attempted request: one server operation, one client TimeoutError.
- Three naive retries of the same payload: three server operations, three client TimeoutErrors.

Identical payload hashes do not create server-side idempotency. The durable ledger reserves before send and returns REPLAY_NO_SEND on a repeated client request ID; it does not claim to cancel or recover the server operation.

An actual subprocess crash follow-up used os._exit after reservation. In one world it exited before send; in the other it exited after receiving the response but before durable settlement. Server operation counts were 0 and 1, while recovered local IN_FLIGHT records were identical. Both restarts refused resend. This sacrifices availability in the unsent world; it is not an exactly-once solution. The package includes the finite indistinguishability proof.

## Two defects in the new bridge, reproduced before fixing

1. An early return for length termination skipped checking an output-token violation. An initially failing regression was retained. Scoring and metering checks are now independent.
2. A nonterminal done=false response's counters could be treated as final usage. An initially failing regression was retained. Such counters now remain unfinalized and the reservation stays unresolved.

The initial exploratory wire result is not the adopted result. Final study results are bound to the revised implementation hashes.

## Implementation boundaries

- Standalone module CLI: `python -m adaptive_evolution_observer.local_text_pair --plan PLAN.json` validates only and performs no network request.
- Actual local evaluation requires explicit `--run-local --output NEW_RUN_DIRECTORY`.
- `--audit --output RUN_DIRECTORY` replays local receipts without network calls.
- Only numeric IPv4 loopback HTTP origins are accepted. No proxy inheritance, redirect follow, automatic retries, model pull, arbitrary tools or generated code execution.
- GET version/tags checks precede and follow POST generation. These are server declarations, not authenticated atomic model snapshots; change-and-change-back remains undetectable.
- SQLite transactions bind request IDs, payload hashes, reservations and settlement. Unknown/in-flight/over-limit requests halt further new admissions. Opening an existing run does not silently re-execute inference.
- Input token reservation is declared, not a proven tokenizer bound. Limits control client admission under the stated reporting contract, not malicious server billing.
- Socket timeout does not imply remote cancellation, strict wall-clock containment or a global budget across new runs.
- No statistical result grants runtime authority. `population_promotion_eligible=false` in this finite fixture work.

## Validation and environment

Baseline: 401 passed. New cases: 69. Final implementation: 470 passed. Fresh applied cumulative package: 470 passed. No failures/errors/skips in those completed suites. These are the delivered subset, not all upstream/Hermes end-to-end tests.

All 54 applied payload hashes matched. Upgrade changed five added files; repeated application changed zero. Unknown local edits were refused and preserved. Applied CLI completed six reviewed requests, offline audit replayed the same evidence, and rerunning inference into the same directory was refused without extra requests.

Python 3.13.5, SQLite/local filesystem, Linux CPU. Clock not pinned; no throughput claim. Stub usage fields are not real LLM token measurements. Runtime-specific source/config/results hashes are in the delivered archive.

## Next long-term gate

An authorized installed local model or independently isolated Hermes runtime is still required. Current container checks found no Hermes/Ollama/container sandbox/model cache and external DNS was unavailable. A connector-capability search did not yield a verified runtime for this slice; this does not assert that every possible external service is unavailable.

Start with text-only paired tasks, fixed model/version and prompt policies, real usage receipts and no generated-code execution. Then validate the specific Hermes wrapper's tool permissions, memory/profile state and full-run usage before R1 production acceptance. Do not substitute this stub for that gate. No continuing job is installed.

## Standalone reproduction

Python 3.11+ and a fresh output path:

```bash
python research/provider_transport_20260910/reproduce_lost_reply.py --output /tmp/lost-reply-example.json
```

It uses only a temporary numeric-loopback HTTP server with reviewed fixed behavior and shuts it down at the end. The source blob was checked against the executed local reproducer.

## Primary interface references

- https://docs.ollama.com/api/generate
- https://docs.ollama.com/api/usage
- https://docs.ollama.com/api/tags
- https://docs.python.org/3/library/http.client.html
- https://hermes-agent.nousresearch.com/docs/guides/python-library

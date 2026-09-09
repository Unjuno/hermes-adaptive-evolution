# R1/R2: explicit evaluation environment and state carryover — 2026-09-09

## Scope

Actual local subprocesses ran finite, reviewed Python repair fixtures. No Hermes/LLM was launched, no provider was called, no workflow was dispatched, and no operational branch or model-facing tool was changed. The baseline is a deliberately memory-assisted reuse-only policy, not a memoryless noop. Candidate is a fixed correct repair that publishes a reusable marker. This tests operational comparison contracts, not model quality or failure prevalence.

The preceding producer already used an explicit environment allowlist and private HOME/TMPDIR. The deliberately shared configurations here are stress controls for generalizing that backend to stateful agents, not proof that its default pure-Python path leaked credentials or state.

## Primary experiment: pristine worktrees are not enough

Three fixture families (clamp, unique, total), four attempts per family, three state surfaces, shared/private settings and both execution orders: 144 pairs. Every arm starts with the same pristine code snapshot. Fixed external verification never reads the policies' mutable memory. No unknown results occurred.

Each table entry is candidate-minus-baseline mean raw success score; each cell has 12 pairs.

| Surface | Shared, baseline first | Shared, candidate first | Private, baseline first | Private, candidate first |
|---|---:|---:|---:|---:|
| HOME | 1.0 | 0.0 | 1.0 | 1.0 |
| HERMES_HOME-like profile | 1.0 | 0.0 | 1.0 | 1.0 |
| XDG cache | 1.0 | 0.0 | 1.0 | 1.0 |

With shared state and candidate first, the baseline reused the repair in all 12 pairs for every surface. Balancing execution order yields 0.5, not the isolated cold-start difference 1.0. These are deterministic fixture controls; repeated attempts are not independent task populations.

## Follow-up 1: all local roots private does not isolate a shared service

A reviewed local file store stands in for an external memory service. It is not a real provider/network experiment. All ordinary local roots are private, but both policies are intentionally given the same surrogate store.

- Baseline first: 12 pairs, raw difference 1.0.
- Candidate first: 12 pairs, raw difference 0.0; baseline memory hit in 12/12.

Therefore local path separation cannot authorize a claim about unverified external state. The runtime validator refuses an unknown external-resource declaration; it does not pretend to authenticate service isolation.

## Follow-up 2: policy hash alone is not an evaluation-cache key

Twelve reviewed controls run the identical noop policy on a repaired input and then a buggy input. Functional scores are 1 then 0. A cache keyed only by policy hash reuses the stale success in 12/12 cases. A key including the input snapshot, metric, runtime, environment contract and initial state avoids all 12 collisions.

This is not a valid paired-policy comparison because inputs intentionally differ; it is a cache-validation counterexample. The delivered runtime does not enable cached-score reuse. Even a full cache hit is not a new independent task. Stochastic seeds, model settings and external service receipts need further binding in a real model backend.

## Implementation disposition

A cumulative conversation package adds execution_environment.py and updates the reviewed producer:

- Fresh empty HOME, HERMES_HOME, XDG cache/config/data/state and temporary roots per subprocess.
- HERMES_REAL_HOME is the private home, not the real user's home. No parent credentials, proxy or arbitrary environment overrides are inherited.
- Startup validation rejects reused/dirty roots, symlinks and undeclared local state.
- Receipts bind local-root identities, empty initial state, environment contract and Python executable/version.
- Metric and evaluation identity incorporate these bindings.
- Audit checks candidate, baseline, external verifier and diagnostic subprocesses, rejecting shared mutable-root identities, runtime mismatches, missing receipts and changed metrics.
- Positive evidence still never grants execution authority.

326 tests passed in one complete implementation run, and all 326 passed again after applying the payload to a fresh directory. This is a delivered subset, NOT the entire upstream/Hermes suite. New tests: 51; previous: 275. Fresh application, previous-package upgrade, idempotent reapplication, all 45 payload hashes and unknown-edit refusal were checked. An applied CLI producer run emitted six policy receipts and three task events; deterministic audit/replay passed with no added duplicate evidence.

The full cumulative plugin code is in the conversation artifact, not merged into an operational branch here. The research reproducer is standalone and standard-library only.

## Limits and negative outcomes retained

This is cold-start evaluation. Useful memory is not inherently contamination: evaluating a learned memory endowment or within-arm learning trajectory requires a different preregistered contract with separately cloned/owned state. Resetting every subprocess is not claimed optimal for such policies.

Private directories, environment variables and same-UID process groups are not an adversarial sandbox. Absolute paths, network, provider memories, daemon caches and hostile code remain outside the guarantee. Hashes do not establish real independence, authentic preregistration or integrity against a party that can rewrite all records. Python executable fingerprints do not cover the complete OS/dependency image.

Local readiness checks found no installed Hermes, Ollama, Docker, Podman or bwrap. No untrusted model program was executed. Initial whole-study launches and one combined test command hit the tool's per-call time limit; no incomplete numerical output was scored. Fixed primary cells were run in bounded chunks and aggregated, then complete test jobs finished before delivery. These orchestration interruptions are retained separately.

## Reproduction

Python 3.11+ on POSIX, standard library only. Python 3.13.5 / SQLite 3.46.1 were used for the implementation tests. CPU clock not pinned; no performance or token-cost claim.

```bash
python research/environment_contract_20260909/reproduce_environment.py --repeats 4 --output /tmp/environment-study.json
python research/environment_contract_20260909/reproduce_environment.py --repeats 4 --followup --output /tmp/external-store-study.json
```

Output paths must be new. Use --cell-index 0 through 11 to run individual primary cells, or 0 through 1 for follow-up cells, when command time limits apply.

Primary implementation references: Python subprocess env/start_new_session documentation and Hermes Profiles/Persistent Memory documentation. Hermes documentation distinguishes HERMES_HOME from the OS HOME used by external tools. That makes the boundary relevant; the numerical results above come from the reviewed local fixtures, not from live Hermes.

- https://docs.python.org/3/library/subprocess.html
- https://hermes-agent.nousresearch.com/docs/user-guide/profiles/
- https://hermes-agent.nousresearch.com/docs/user-guide/features/memory

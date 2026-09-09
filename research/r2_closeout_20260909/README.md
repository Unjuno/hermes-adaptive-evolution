# R1/R2 episode closeout and long-term gates — 2026-09-09

## Scope

This work completed a bounded local roadmap slice, not the full production roadmap. No real Hermes/LLM or paid provider task ran, no workflow was explicitly dispatched, and no operational branch was merged. The cumulative runtime package is delivered as a conversation artifact. This research branch contains a standalone statistical reproducer, a tested hardening patch and this status; it does not imply that all previous R2 runtime files were integrated into the operational plugin.

## Local milestones closed

- L0: expand and hash the two preceding packages; reproduce all 340 existing tests in one run.
- L1: reproduce new faults, add regression tests, and repair EpisodeProtocol.
- L2: execute finite reviewed stateful policies through actual subprocesses, independent scoring, episode aggregation and external CLI replay.
- L3: apply the cumulative package in a fresh directory, rerun the full delivered subset, check upgrade, idempotency, unknown-edit refusal and payload hashes.

L0–L3 are local work items contributing to R0/R2, not a renaming of global production completion.

## Defects actually reproduced in the delivered previous implementation

1. `report()["state_contract"]` exposed an internal dictionary. Mutating the returned report changed the initial-state condition without changing the protocol hash. A task claiming the altered initial state was accepted.
2. The first late task was journaled but not included in the in-time event map. A subsequent late task could not validate its state predecessor, so the receipt chain stopped.
3. Injecting a failure after evidence update left partially updated clock, closed episodes or evidence. Rejection was not exception-atomic.
4. List/dict trial IDs raised TypeError rather than the declared contract error.

The old 340 tests passed. Adding 37 regression cases produced 6 failures on old code. Repairs use a defensive report copy, a separate all-receipt state chain, staged state publication and strict type validation. The revised engine preserves the v0.1 measurement schema and reports implementation revision 0.2.0. The patch in this directory targets the previous conversation-delivered EpisodeProtocol, not a presumed operational file.

The engine remains a bounded, single-writer offline replay engine. Copying staged dictionaries has a cost; no streaming throughput claim is made. Exception-atomic object updates are not a process-crash or concurrent database guarantee.

## Actual reviewed stateful execution

Candidate: fixed LRU capacity 2. Baseline: fixed LRU capacity 1. The programs are hand-reviewed, not model-generated. Prediction runs before feedback is written; a separate parent checks predictions, scores and the declared memory update. Each arm/episode has private persistent memory, while subprocess HOME/profile/cache roots are fresh. Episode starts are reset.

96 subprocesses -> 48 policy steps -> 24 task pairs -> 3 episode evidence units.

| Sequence | Candidate success | Baseline success |
|---|---:|---:|
| blocked | .75 | .75 |
| alternating | .75 | .00 |
| mixed | .75 | .25 |

The three fixed sequences are descriptive operational controls, not a sample supporting population performance inference. `population_promotion_eligible=false` and `execution_authorized=false`. The saved report equals external CLI replay; duplicate event replay adds zero evidence. Actual applied-code production and audit also passed.

## Follow-up: clustering and weighting answer different questions

Both methods use exactly 120 independent episodes in every simulated world; neither treats inner task rows as independent. Episode effect is +.8 or -.8 with equal probability. Positive episodes have nine tasks and negative episodes one task.

The equal-episode target is 0. The equal-task long-run target is E[N*D]/E[N] = 3.2/5 = .64. These are different legitimate targets. Testing the second does not prove improvement in the first.

Prespecified betting mixture [0,.02,.05,.1,.2,.4,.8], alpha .05, 4000 worlds per condition:

- Primary positive-long condition: episode-target crossing 53/4000; task-target crossing 4000/4000.
- Fresh-seed positive-long follow-up: 46/4000 versus 4000/4000.
- Independent-length and negative-long controls were also run.

The task-target positives are NOT universal false positives: the true task target is positive. The problem is silently changing estimands. The task-target test feeds bounded N*D/9, one contribution per episode. Finite-sample ratios are not equated with the population ratio. Result files include Wilson intervals; endpoints can have tiny floating-point roundoff around 1.

## Tests and package validation

- Baseline subset: 340 passed.
- Revised implementation: 401 passed, zero failures/errors/skips.
- Fresh cumulative application: the same 401 passed in one command.
- New cases: 37 episode regressions and 24 reviewed producer checks.
- All 49 applied payload hashes matched.
- Previous-package upgrade passed; second application changed zero files.
- An unknown local edit was refused and preserved.
- Applied-code reviewed producer and deterministic audit passed.

This is the delivered subset, NOT the entire upstream/Hermes suite. Test runtime: Python 3.13.5 on POSIX, AMD EPYC 9V74. Clock not pinned; no GPU/LLM/throughput claim. A private no-pip virtual environment avoided unrelated system startup hooks without skipping tests.

## Long-term roadmap retained

| Gate | Completion condition | Current state |
|---|---|---|
| R0 | adopted claims tied to reproducible source/config/results | local delivered subset checked; historical full corpus integration not claimed |
| R1 | observable, causally valid real-task metrics and measured costs | synthetic/fixture checks only; real model value unresolved |
| R2 | non-executing proposals/evidence/state ledger connected to valid producer | reviewed stateful loop complete locally; live Hermes producer pending |
| R3 | fixed versus adaptive confirmation compared at equal risk and cost | statistical contracts exist; adaptive operational commit unresolved |
| R4 | bounded allocator and approved reversible canary | not started |
| R5 | unseen-task acceptance, recovery and release/CI contracts | not complete |

Local readiness checks found no hermes, ollama, docker, podman or bwrap executable. This is not a claim that every possible external service is unavailable. It means no reviewed isolated real-provider backend was provisioned for this work slice. Runtime authority, credentials and spending are not self-assigned. No continuing background job is installed.

## Reproduce

With Python and NumPy available, from this directory:

```bash
python episode_weighting_study.py --output /tmp/episode-weighting-main.json
python episode_weighting_study.py --seed 2026090932 --output /tmp/episode-weighting-followup.json
```

Use new output paths. The complete patch package includes prior runtime dependencies, 401 tests, original failing regressions, plans, proof variable tables, per-step receipts and a guarded apply script. The hardening patch alone is not that full package.

## Limits

Local hashes and timestamps are consistency evidence, not authenticated independence, true state contents or honest preregistration. Same-user subprocesses are not hostile-code or network containment. Episode aggregation does not remove shared upstream confounding. Unrestricted cross-family alpha reset remains outside the guarantee. The next gate is independently isolated real Hermes paired evaluation, not another unbounded expansion of synthetic mechanisms.

Primary statistical foundation: Waudby-Smith and Ramdas, Estimating means of bounded random variables by betting, DOI 10.1093/jrsssb/qkad009, arXiv:2010.09686. These are applications and finite counterexamples, not a new universal inference theorem.

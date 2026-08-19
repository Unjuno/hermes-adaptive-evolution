# E1 deterministic repair fixture

This directory is intentionally broken. It exists only to generate a small,
repeatable provider-backed Hermes trace for E1.

## Baseline

From this directory:

```bash
python -m unittest -q
```

must fail because `counter.advance()` contains a deliberate off-by-one error.
The correct implementation is the smallest patch that makes the four tests
pass without changing the tests.

## Required Hermes behavior for the E1 trace

The root agent should be instructed to:

1. use `delegate_task` exactly once with a leaf child;
2. ask the child to reproduce the failing test before editing;
3. make the smallest root-cause patch in `counter.py` only;
4. run `python -m unittest -q` after the patch;
5. report the observed failure and final passing result.

A suitable task prompt is:

```text
This is an E1 observability fixture. Use delegate_task exactly once with a leaf
subagent. Ask the child to reproduce the failing unittest before editing, fix
the root cause with the smallest change, run `python -m unittest -q`, and
return the evidence. Do not modify the tests. After the child returns, inspect
the result and report whether the test transitioned from failing to passing.
```

The purpose is not to benchmark coding ability. The purpose is to capture a
stable lifecycle containing root execution, delegation, child identity, tool
activity, a reproducible failure, recovery, and completion.

## Reset

After a run, restore this fixture before another capture:

```bash
git restore experiments/fixtures/e1_repair_project/counter.py
```

Do not commit the repaired fixture to `main`; the failing baseline is the test
instrument.

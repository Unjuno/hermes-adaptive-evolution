# E1 provider-backed Hermes runbook

E1 is the first provider-backed gate for `hermes-adaptive-evolution`. It is an
**observability-contract experiment**, not a coding benchmark and not an
authorization to enable adaptive organization changes.

## Goal

Produce one real Hermes capture with this lifecycle:

```text
root session
  -> delegate_task exactly once
  -> leaf child
  -> deterministic failing unittest
  -> minimal repair
  -> passing unittest
  -> child completion
```

The expected outcome is a portable capture bundle that passes
`experiments/validate_e1_capture.py`, plus field-coverage and corruption reports.

## Safety boundary

Run E1 in an expendable container/VM or similarly isolated workspace. The
observer itself is hook-only and does not add model-facing tools, but Hermes is
still a coding agent with ordinary filesystem/terminal capabilities.

Do not use broad `--yolo` permissions on a personal/work filesystem. If you use
`--yolo` to make a one-shot run non-interactive, do it only inside an external
sandbox whose filesystem and credentials are disposable/minimal.

## 1. Install and enable the plugin

From this repository:

```bash
python -m pip install -e .
hermes plugins enable adaptive-evolution
hermes plugins doctor . --ci
```

Hermes third-party general plugins are opt-in. `hermes plugins enable <name>`
adds the plugin to the active profile allow-list.

Record versions before the run:

```bash
hermes --version
python -c "import importlib.metadata as m; print(m.version('hermes-adaptive-evolution'))"
```

## 2. Create an isolated fixture workspace

Do not repair the copy tracked by this repository. Copy it to a disposable
directory:

```bash
E1_ROOT="$(mktemp -d)"
cp -R experiments/fixtures/e1_repair_project "$E1_ROOT/project"
cd "$E1_ROOT/project"
```

Confirm the deterministic precondition:

```bash
python -m unittest -q
```

This command **must fail** before the Hermes run. If it passes, stop: the E1
fixture is not in its intended baseline state.

## 3. Choose an observer DB explicitly

```bash
export ADAPTIVE_EVOLUTION_OBSERVER_DB="$E1_ROOT/observer.sqlite3"
unset ADAPTIVE_EVOLUTION_CAPTURE_CONTENT
```

The second command makes the intended privacy state explicit: prompt/tool/API
content is not retained by the observer.

## 4. Run Hermes

Use the provider/model already configured for the active Hermes profile. Hermes
supports one-shot execution with `-z/--oneshot` and `hermes chat -q`.

Suggested prompt:

```text
This is an E1 observability fixture. Use delegate_task exactly once with a leaf
subagent. Ask the child to reproduce the failing unittest before editing, fix
the root cause with the smallest change, run `python -m unittest -q`, and
return the evidence. Do not modify the tests. After the child returns, inspect
the result and report whether the test transitioned from failing to passing.
```

Example one-shot invocation:

```bash
PROMPT="$(cat <<'EOF'
This is an E1 observability fixture. Use delegate_task exactly once with a leaf
subagent. Ask the child to reproduce the failing unittest before editing, fix
the root cause with the smallest change, run `python -m unittest -q`, and
return the evidence. Do not modify the tests. After the child returns, inspect
the result and report whether the test transitioned from failing to passing.
EOF
)"
hermes -z "$PROMPT"
```

If your environment requires command approval, use the normal approval flow.
Only use `--yolo` when the **external sandbox**, not the prompt, provides the
hard safety boundary.

## 5. Verify the repaired fixture independently

Do not trust the final natural-language answer as the test oracle:

```bash
python -m unittest -q
```

This command must now pass, and `test_counter.py` must remain unchanged.

## 6. Create an immutable capture bundle

```bash
adaptive-evolution-observer \
  --db "$ADAPTIVE_EVOLUTION_OBSERVER_DB" \
  bundle "$E1_ROOT/capture"

adaptive-evolution-observer replay "$E1_ROOT/capture"
```

The bundle contains pre-sanitized raw events and their normalized derived view,
not the SQLite database.

## 7. Run the machine E1 gate

```bash
python /path/to/hermes-adaptive-evolution/experiments/validate_e1_capture.py \
  "$E1_ROOT/capture" \
  --output "$E1_ROOT/e1-validation.json"
```

Required checks include:

- bundle replay/checksum consistency;
- content capture disabled;
- at least one delegation start/stop;
- at least one observed tool error;
- a later same-agent tool success;
- no unresolved session identity in the complete capture;
- reconstructed parent->child interaction state.

A pass means **M1 provider-backed observability path exists**. It does not mean
role mixing/diffusivity are useful routing variables; that is M2.

## 8. Produce E1/E2 diagnostic reports

```bash
python /path/to/hermes-adaptive-evolution/experiments/report_hook_coverage.py \
  "$E1_ROOT/capture" \
  --output "$E1_ROOT/hook-coverage.json"

python /path/to/hermes-adaptive-evolution/experiments/run_capture_corruption.py \
  "$E1_ROOT/capture" \
  --replicates 50 \
  --output "$E1_ROOT/corruption-summary.json"
```

Do not turn one capture's field fractions, event counts, or corruption tolerance
into production thresholds. They are evidence for the next experiment design.

## 9. What would justify a Hermes fork investigation?

E1 should record a missing-primitive issue only if all of these hold:

1. the primitive changes a concrete routing/safety decision;
2. it is absent on the relevant real execution path;
3. it cannot be reconstructed from existing correlation/event fields;
4. an alternative observable does not provide equivalent decision utility.

Otherwise remain a standalone Hermes plugin.

# hermes-adaptive-evolution

Independent research framework and **Hermes Agent plugin** for adaptive multi-agent organization, trajectory observability, safe self-repair, skill evolution, and later model specialization.

> Status: **experimental / diagnostic-only**. The current `v0.2` slice observes Hermes through public plugin hooks; it does not autonomously reconfigure the runtime yet.

## Why a Hermes plugin first

Hermes already provides the execution runtime, tools, sessions, subagents, Skills, and plugin hooks. This project keeps adaptation logic outside Hermes core and only considers a fork if a live experiment proves that a decision-relevant primitive is unavailable through the public plugin boundary.

Current flow:

```text
Hermes execution
      ↓ public observer hooks
metadata-first event recorder
      ↓
normalization / correlation
      ↓
Organization State Estimator
      ├─ functional-role posterior
      ├─ traffic-weighted role mixing
      ├─ directed diffusivity
      └─ policy fragility proxy
      ↓
future: task-conditioned organization router
```

## Current plugin tools

- `adaptive_evolution_observer_status` — replay captured events and return the current experimental organization state.
- `adaptive_evolution_observer_export` — export normalized/deduplicated events as JSONL.

The returned state is explicitly `diagnostic_only`. No synthetic event-count threshold authorizes organization changes.

## Privacy boundary

The recorder is metadata-first. Prompt text, child goals, tool args/results, API content, error text, and common secret fields are omitted/redacted by default before persistence.

Set `ADAPTIVE_EVOLUTION_CAPTURE_CONTENT=1` only in an expendable test environment.

## Install

### Editable Python plugin

```bash
python -m pip install -e .
```

The package declares the `hermes_agent.plugins` entry point `adaptive-evolution`.

### Hermes directory-plugin shape

The repository root also contains `plugin.yaml` and `__init__.py`, so a trusted checkout can be linked into the Hermes plugin directory:

```bash
mkdir -p ~/.hermes/plugins
ln -s /path/to/hermes-adaptive-evolution ~/.hermes/plugins/adaptive-evolution
```

When using the directory form, install this project's Python dependencies in the same environment first.

## State

The default observer database is profile-aware:

```text
$HERMES_HOME/adaptive-evolution/observer.sqlite3
```

When `HERMES_HOME` is unset, this resolves to:

```text
~/.hermes/adaptive-evolution/observer.sqlite3
```

Override it explicitly with:

```bash
export ADAPTIVE_EVOLUTION_OBSERVER_DB=/path/to/observer.sqlite3
```

or move all adaptive-evolution data with:

```bash
export ADAPTIVE_EVOLUTION_DATA_DIR=/path/to/data-dir
```

## Capture and replay workflow

After a Hermes run, inspect the observer database without asking the observed agent to call an analysis tool:

```bash
adaptive-evolution-observer --db "$HERMES_HOME/adaptive-evolution/observer.sqlite3" status
```

A plain normalized JSONL export is available when that is all you need:

```bash
adaptive-evolution-observer --db "$HERMES_HOME/adaptive-evolution/observer.sqlite3" export ./trace.jsonl
```

For experiments, prefer a **capture bundle**:

```bash
adaptive-evolution-observer --db "$HERMES_HOME/adaptive-evolution/observer.sqlite3" bundle ./capture-001
adaptive-evolution-observer replay ./capture-001
```

Bundle schema `adaptive-evolution.capture-bundle.v0.2` contains:

```text
capture-001/
├── manifest.json
├── sanitized-raw-events.jsonl
└── normalized-events.jsonl
```

The raw stream in the bundle is already sanitized before leaving SQLite. Both event streams have SHA-256 checksums, the raw SQLite database is not included, and replay verifies that re-normalization and organization state still match the manifest.

### E2 corruption experiments

Once a real Hermes capture exists, use the same immutable sanitized event stream to measure robustness against telemetry corruption:

```bash
python experiments/run_capture_corruption.py ./capture-001 \
  --replicates 50 \
  --output ./capture-001-corruption.json
```

Current scenarios include:

- 1/5/10% duplicate injection;
- 1/5/10% event drop;
- full event reorder;
- 1/5/10% optional correlation-ID stripping.

The experiment reports distributions of identity uncertainty, normalized event loss, interaction-count error, role-mixing error, diffusivity error, role-entropy error, and fragility error. These results are explicitly `experiment_only`; no synthetic or single-capture threshold enables organization reconfiguration.

This separation is deliberate: the system being observed does not need to participate in analysis of its own telemetry.

## Research direction

The current working hypotheses are deliberately falsifiable:

1. multi-agent organization can often be represented more cheaply as bounded local stochastic interactions than as an unrestricted graph search;
2. coarse organization variables such as role mixing and diffusivity can be decision-relevant, but only after they are observable on real Hermes traces;
3. fine-grained policy/topology corrections should activate only when evidence supports them;
4. task-conditioned routing should be evaluated with paired and stratified benchmarks, not a single global score;
5. rare failures and distribution shift require separate stress suites.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`experiments/EXPERIMENT_PLAN.md`](experiments/EXPERIMENT_PLAN.md).

## Development

```bash
python -m pytest
python -m compileall -q adaptive_evolution_observer __init__.py
```

For the real Hermes contract path (requires `hermes-agent==0.20.4`):

```bash
hermes plugins doctor . --ci
python scripts/check_hermes_contract.py
python scripts/check_hermes_delegate_hooks.py
```

The dedicated `hermes-contract` workflow runs the directory-plugin contract before installing this repository as a Python distribution, then validates the pip entry point and an offline real-Hermes `delegate_task` lifecycle.

## License

Apache-2.0. This is an independent research project built for use with Hermes Agent; it is not an official Nous Research project.

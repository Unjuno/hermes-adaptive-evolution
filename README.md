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

Default observer database:

```text
~/.hermes/adaptive-evolution/observer.sqlite3
```

Override it with:

```bash
export ADAPTIVE_EVOLUTION_OBSERVER_DB=/path/to/observer.sqlite3
```

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

## License

Apache-2.0. This is an independent research project built for use with Hermes Agent; it is not an official Nous Research project.

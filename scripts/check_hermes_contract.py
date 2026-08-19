from __future__ import annotations

import importlib.metadata
import json

from adaptive_evolution_observer.plugin import HOOKS


def main() -> int:
    from hermes_cli.plugins import VALID_HOOKS

    invalid = sorted(set(HOOKS) - set(VALID_HOOKS))
    entry_points = {
        ep.name: ep for ep in importlib.metadata.entry_points(group="hermes_agent.plugins")
    }
    ep = entry_points.get("adaptive-evolution")
    if ep is None:
        raise SystemExit("adaptive-evolution entry point was not discovered")
    loaded = ep.load()
    register = getattr(loaded, "register", None)
    if not callable(register):
        raise SystemExit("adaptive-evolution entry point does not expose callable register")
    if invalid:
        raise SystemExit(f"observer registers hooks not supported by this Hermes: {invalid}")

    result = {
        "hermes_agent_version": importlib.metadata.version("hermes-agent"),
        "plugin_distribution_version": importlib.metadata.version("hermes-adaptive-evolution"),
        "entry_point": ep.value,
        "observer_hooks": list(HOOKS),
        "invalid_hooks": invalid,
        "result": "compatible",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

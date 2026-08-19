from __future__ import annotations

from pathlib import Path

from adaptive_evolution_observer.plugin import HOOKS


def _declared_hooks() -> tuple[str, ...]:
    lines = Path("plugin.yaml").read_text(encoding="utf-8").splitlines()
    hooks = []
    inside = False
    for raw in lines:
        line = raw.rstrip()
        if line == "provides_hooks:":
            inside = True
            continue
        if inside:
            if line.startswith("  - "):
                hooks.append(line[4:].strip())
                continue
            if line and not line.startswith(" "):
                break
    return tuple(hooks)


def test_manifest_declares_exact_observer_hook_surface():
    assert set(_declared_hooks()) == set(HOOKS)


def test_manifest_keeps_m1_m2_hook_only():
    text = Path("plugin.yaml").read_text(encoding="utf-8")
    assert "provides_tools:" not in text

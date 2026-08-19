from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch


def _parent() -> MagicMock:
    parent = MagicMock()
    parent.base_url = "https://openrouter.ai/api/v1"
    parent.api_key = "test-key"
    parent.provider = "openrouter"
    parent.api_mode = "chat_completions"
    parent.model = "test-model"
    parent.platform = "cli"
    parent.providers_allowed = None
    parent.providers_ignored = None
    parent.providers_order = None
    parent.provider_sort = None
    parent.enabled_toolsets = ["terminal", "file"]
    parent.disabled_toolsets = []
    parent._session_db = None
    parent._delegate_depth = 0
    parent._active_children = []
    parent._active_children_lock = threading.Lock()
    parent._print_fn = None
    parent.tool_progress_callback = None
    parent.thinking_callback = None
    parent._memory_manager = None
    parent.session_id = "parent-session"
    parent._current_turn_id = "parent-turn"
    parent.session_estimated_cost_usd = 0.0
    return parent


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adaptive-evolution-hermes-") as td:
        root = Path(td)
        home = root / "hermes-home"
        home.mkdir(parents=True)
        db = root / "observer.sqlite3"
        (home / "config.yaml").write_text(
            "plugins:\n  enabled:\n    - adaptive-evolution\n",
            encoding="utf-8",
        )
        os.environ["HERMES_HOME"] = str(home)
        os.environ["ADAPTIVE_EVOLUTION_OBSERVER_DB"] = str(db)

        from hermes_cli import plugins

        original_manager = plugins._plugin_manager
        try:
            manager = plugins.PluginManager()
            plugins._plugin_manager = manager
            manager.discover_and_load()

            loaded = None
            for key, candidate in manager._plugins.items():
                if key == "adaptive-evolution" or candidate.manifest.name == "adaptive-evolution":
                    loaded = candidate
                    break
            if loaded is None:
                raise SystemExit("adaptive-evolution was not discovered by real PluginManager")
            if not loaded.enabled or loaded.error:
                raise SystemExit(
                    f"adaptive-evolution failed to enable: enabled={loaded.enabled} error={loaded.error!r}"
                )
            for hook in ("subagent_start", "subagent_stop"):
                if not manager.has_hook(hook):
                    raise SystemExit(f"real PluginManager has no registered {hook} callback")

            from tools.delegate_tool import delegate_task

            child = MagicMock()
            child.session_id = "child-session"
            child._delegate_saved_tool_names = []
            child._credential_pool = None
            child._delegate_role = "leaf"
            child.session_estimated_cost_usd = 0.0

            with (
                patch("run_agent.AIAgent", return_value=child),
                patch("tools.delegate_tool._run_single_child") as run_child,
            ):
                run_child.return_value = {
                    "task_index": 0,
                    "status": "completed",
                    "summary": "offline contract fixture completed",
                    "api_calls": 1,
                    "duration_seconds": 0.01,
                    "_child_role": "leaf",
                    "tool_trace": [
                        {
                            "tool": "python",
                            "args_bytes": 16,
                            "result_bytes": 2,
                            "status": "ok",
                            "input_summary": {"argument_keys": ["code"], "targets": {}},
                        }
                    ],
                }
                raw = delegate_task(
                    goal="Exercise the real Hermes delegation lifecycle without an LLM call",
                    parent_agent=_parent(),
                )

            result = json.loads(raw)
            if "error" in result:
                raise SystemExit(f"delegate_task returned an error: {result['error']}")

            from adaptive_evolution_observer.cli import status
            from adaptive_evolution_observer.store import EventStore

            rows = EventStore(db).load()
            hooks = [row["hook"] for row in rows]
            if "subagent_start" not in hooks or "subagent_stop" not in hooks:
                raise SystemExit(f"observer did not persist delegation lifecycle hooks: {hooks}")

            report = status(db)
            state = report["state"]
            if state["interaction_events"] < 1:
                raise SystemExit(f"replay did not reconstruct a parent->child interaction: {state}")
            if report["events"]["uncertain_session_events"]:
                raise SystemExit(
                    "complete offline delegation fixture produced uncertain session identity: "
                    f"{report['events']}"
                )

            print(json.dumps({
                "result": "compatible",
                "loaded_plugin_key": loaded.manifest.key or loaded.manifest.name,
                "captured_hooks": hooks,
                "event_diagnostics": report["events"],
                "organization_state": state,
            }, indent=2, sort_keys=True))
            return 0
        finally:
            plugins._plugin_manager = original_manager


if __name__ == "__main__":
    raise SystemExit(main())

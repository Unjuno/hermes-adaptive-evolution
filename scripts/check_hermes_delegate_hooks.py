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
            for hook in ("subagent_start", "subagent_stop", "post_tool_call", "api_request_error"):
                if not manager.has_hook(hook):
                    raise SystemExit(f"real PluginManager has no registered {hook} callback")

            from hermes_cli.lifecycle import invoke_hook
            from tools.delegate_tool import delegate_task

            invoke_hook(
                "on_session_start",
                session_id="parent-session",
                task_id="parent-task",
                turn_id="parent-turn",
                model="test-model",
                platform="cli",
            )

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

            # Exercise additive real-Hermes lifecycle dispatch beyond delegation.
            # These events intentionally arrive after subagent_stop: the observer
            # normalizer must correlate by child_session_id independent of order.
            invoke_hook(
                "post_tool_call",
                session_id="child-session",
                task_id="child-task",
                turn_id="child-turn-1",
                tool_call_id="tool-call-1",
                api_request_id="api-request-1",
                tool_name="python",
                args={"code": "print('secret')", "api_key": "super-secret"},
                result="sensitive tool output",
                status="success",
                duration_ms=2,
            )
            invoke_hook(
                "api_request_error",
                session_id="child-session",
                task_id="child-task",
                turn_id="child-turn-2",
                api_request_id="api-request-2",
                provider="offline-test",
                model="test-model",
                status_code=500,
                retry_count=1,
                max_retries=2,
                retryable=True,
                reason="synthetic upstream failure",
                error="sensitive provider error",
            )
            invoke_hook(
                "on_skill_lifecycle",
                session_id="child-session",
                task_id="child-task",
                action="used",
                skill_name="fixture-skill",
                provenance="test",
                use_count=1,
                reused=False,
                reuse_after_patch=False,
            )
            invoke_hook(
                "kanban_task_claimed",
                task_id="kanban-1",
                profile_name="default",
                board="fixture",
                assignee="worker-1",
                run_id="run-1",
            )
            invoke_hook(
                "kanban_task_completed",
                task_id="kanban-1",
                profile_name="default",
                board="fixture",
                assignee="worker-1",
                run_id="run-1",
                summary="sensitive completion detail",
            )
            invoke_hook(
                "on_session_end",
                session_id="parent-session",
                task_id="parent-task",
                turn_id="parent-turn",
                completed=True,
                failed=False,
                interrupted=False,
                model="test-model",
                platform="cli",
            )

            from adaptive_evolution_observer.bundle import create_bundle
            from adaptive_evolution_observer.cli import status
            from adaptive_evolution_observer.store import EventStore

            rows = EventStore(db).load()
            hooks = [row["hook"] for row in rows]
            required = {
                "on_session_start",
                "subagent_start",
                "subagent_stop",
                "post_tool_call",
                "api_request_error",
                "on_skill_lifecycle",
                "kanban_task_claimed",
                "kanban_task_completed",
                "on_session_end",
            }
            missing = sorted(required - set(hooks))
            if missing:
                raise SystemExit(f"observer did not persist required real-Hermes hooks: {missing}; got={hooks}")

            serialized_rows = json.dumps(rows, ensure_ascii=False)
            if "super-secret" in serialized_rows or "sensitive tool output" in serialized_rows:
                raise SystemExit("metadata-first recorder leaked intentionally sensitive fixture content")

            report = status(db)
            state = report["state"]
            if state["interaction_events"] < 1:
                raise SystemExit(f"replay did not reconstruct a parent->child interaction: {state}")
            if state["tool_outcomes"] < 1:
                raise SystemExit(f"replay did not reconstruct tool outcome evidence: {state}")
            if report["events"]["uncertain_session_events"]:
                raise SystemExit(
                    "complete offline delegation fixture produced uncertain session identity: "
                    f"{report['events']}"
                )

            contract_report = {
                "result": "compatible",
                "loaded_plugin_key": loaded.manifest.key or loaded.manifest.name,
                "captured_hooks": hooks,
                "event_diagnostics": report["events"],
                "organization_state": state,
            }

            artifact_dir = os.getenv("ADAPTIVE_EVOLUTION_CONTRACT_ARTIFACT_DIR")
            if artifact_dir:
                capture_dir = Path(artifact_dir).expanduser()
                capture_dir.parent.mkdir(parents=True, exist_ok=True)
                create_bundle(db, capture_dir)
                (capture_dir.parent / "offline-contract-report.json").write_text(
                    json.dumps(contract_report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

            print(json.dumps(contract_report, indent=2, sort_keys=True))
            return 0
        finally:
            plugins._plugin_manager = original_manager


if __name__ == "__main__":
    raise SystemExit(main())

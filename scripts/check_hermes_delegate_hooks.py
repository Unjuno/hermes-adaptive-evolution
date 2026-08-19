from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

TOOL_SUCCESS_STATUSES = frozenset({"ok", "success"})


def _parent() -> SimpleNamespace:
    """Strict-ish parent fixture for the current Hermes delegation surface.

    Unlike MagicMock, missing direct attributes raise instead of being silently
    fabricated. Most optional Hermes fields are consumed through getattr(...,
    default), so this keeps the fixture small while making upstream contract
    drift visible.
    """
    return SimpleNamespace(
        base_url="https://openrouter.ai/api/v1",
        api_key="test-key",
        provider="openrouter",
        api_mode="chat_completions",
        model="test-model",
        platform="cli",
        providers_allowed=None,
        providers_ignored=None,
        providers_order=None,
        provider_sort=None,
        provider_require_parameters=False,
        provider_data_collection=None,
        openrouter_min_coding_score=None,
        request_overrides={},
        enabled_toolsets=["terminal", "file"],
        disabled_toolsets=[],
        _session_db=None,
        _delegate_depth=0,
        _subagent_id=None,
        _active_children=[],
        _active_children_lock=threading.Lock(),
        _print_fn=None,
        tool_progress_callback=None,
        thinking_callback=None,
        _memory_manager=None,
        session_id="parent-session",
        _current_turn_id="parent-turn",
        session_estimated_cost_usd=0.0,
        reasoning_config=None,
        prefill_messages=None,
        _fallback_chain=None,
        acp_command=None,
        acp_args=[],
        max_tokens=None,
    )


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
            from model_tools import handle_function_call
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

            # Exercise the real Hermes terminal dispatch and post_tool_call
            # semantics. Upstream treats non-zero terminal exit codes as
            # status=error/error_type=tool_error even though the tool handler
            # itself returned structured output. The observer can therefore
            # capture failure -> recovery without retaining command/output text.
            failed_raw = handle_function_call(
                "terminal",
                {"command": "python -c \"import sys; sys.exit(7)\""},
                task_id="child-task",
                session_id="child-session",
                tool_call_id="terminal-fail",
            )
            recovered_raw = handle_function_call(
                "terminal",
                {"command": "python -c \"print('fixture recovered')\""},
                task_id="child-task",
                session_id="child-session",
                tool_call_id="terminal-recovered",
            )
            failed_result = json.loads(failed_raw)
            recovered_result = json.loads(recovered_raw)
            if int(failed_result.get("exit_code", 0)) == 0:
                raise SystemExit(f"terminal failure fixture unexpectedly succeeded: {failed_result}")
            if int(recovered_result.get("exit_code", 1)) != 0:
                raise SystemExit(f"terminal recovery fixture unexpectedly failed: {recovered_result}")

            # Exercise additive real-Hermes lifecycle dispatch beyond tool and
            # delegation. These events arrive after subagent_stop; two-pass
            # normalization must still map the child session correctly.
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

            terminal_events = {
                row["payload"].get("tool_call_id"): row["payload"]
                for row in rows
                if row["hook"] == "post_tool_call"
                and row["payload"].get("tool_call_id") in {"terminal-fail", "terminal-recovered"}
            }
            fail_event = terminal_events.get("terminal-fail")
            recovery_event = terminal_events.get("terminal-recovered")
            if not fail_event or fail_event.get("status") != "error" or fail_event.get("error_type") != "tool_error":
                raise SystemExit(f"non-zero terminal exit was not observed as tool_error: {fail_event}")
            recovery_status = str((recovery_event or {}).get("status") or "").strip().lower()
            if not recovery_event or recovery_status not in TOOL_SUCCESS_STATUSES:
                raise SystemExit(
                    f"terminal recovery was not observed as a recognized success status "
                    f"{sorted(TOOL_SUCCESS_STATUSES)}: {recovery_event}"
                )

            serialized_rows = json.dumps(rows, ensure_ascii=False)
            for secret in (
                "fixture recovered",
                "sys.exit(7)",
                "sensitive provider error",
                "sensitive completion detail",
            ):
                if secret in serialized_rows:
                    raise SystemExit(f"metadata-first recorder leaked fixture content: {secret!r}")

            report = status(db)
            state = report["state"]
            if state["interaction_events"] < 1:
                raise SystemExit(f"replay did not reconstruct a parent->child interaction: {state}")
            if state["tool_outcomes"] < 2:
                raise SystemExit(f"replay did not reconstruct failure/recovery tool evidence: {state}")
            if report["events"]["uncertain_session_events"]:
                raise SystemExit(
                    "complete offline delegation fixture produced uncertain session identity: "
                    f"{report['events']}"
                )

            contract_report = {
                "result": "compatible",
                "loaded_plugin_key": loaded.manifest.key or loaded.manifest.name,
                "captured_hooks": hooks,
                "terminal_failure_status": fail_event.get("status"),
                "terminal_failure_type": fail_event.get("error_type"),
                "terminal_recovery_status": recovery_event.get("status"),
                "recognized_tool_success_statuses": sorted(TOOL_SUCCESS_STATUSES),
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

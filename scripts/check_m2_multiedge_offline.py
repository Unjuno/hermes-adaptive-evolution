from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _parent() -> SimpleNamespace:
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
        session_id="m2-parent-session",
        _current_turn_id="m2-parent-turn",
        session_estimated_cost_usd=0.0,
        reasoning_config=None,
        prefill_messages=None,
        _fallback_chain=None,
        acp_command=None,
        acp_args=[],
        max_tokens=None,
    )


def _child(session_id: str) -> MagicMock:
    child = MagicMock()
    child.session_id = session_id
    child._delegate_saved_tool_names = []
    child._credential_pool = None
    child._delegate_role = "leaf"
    child.session_estimated_cost_usd = 0.0
    return child


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adaptive-evolution-m2-") as td:
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
            loaded = next(
                (
                    candidate
                    for key, candidate in manager._plugins.items()
                    if key == "adaptive-evolution" or candidate.manifest.name == "adaptive-evolution"
                ),
                None,
            )
            if loaded is None or not loaded.enabled or loaded.error:
                raise SystemExit(f"adaptive-evolution unavailable: {loaded!r}")

            from hermes_cli.lifecycle import invoke_hook
            from model_tools import handle_function_call
            from tools.delegate_tool import delegate_task

            invoke_hook(
                "on_session_start",
                session_id="m2-parent-session",
                task_id="m2-task",
                turn_id="m2-parent-turn",
                model="test-model",
                platform="cli",
            )

            parent = _parent()
            children = [_child("m2-child-a"), _child("m2-child-b")]
            child_results = [
                {
                    "task_index": 0,
                    "status": "completed",
                    "summary": "diagnosis complete",
                    "api_calls": 1,
                    "duration_seconds": 0.01,
                    "_child_role": "leaf",
                    "tool_trace": [],
                },
                {
                    "task_index": 0,
                    "status": "completed",
                    "summary": "repair complete",
                    "api_calls": 1,
                    "duration_seconds": 0.01,
                    "_child_role": "leaf",
                    "tool_trace": [],
                },
            ]

            with (
                patch("run_agent.AIAgent", side_effect=children),
                patch("tools.delegate_tool._run_single_child", side_effect=child_results),
            ):
                for goal in (
                    "Diagnose the deterministic fixture without editing",
                    "Repair the deterministic fixture and verify it",
                ):
                    raw = delegate_task(goal=goal, parent_agent=parent)
                    result = json.loads(raw)
                    if "error" in result:
                        raise SystemExit(f"delegate_task failed: {result['error']}")

            # Add distinct outcome evidence through the real Hermes terminal
            # dispatcher, while keeping topology solely from real delegation
            # start/stop lifecycle events.
            handle_function_call(
                "terminal",
                {"command": "python -c \"print('diagnosis evidence')\""},
                task_id="m2-task-a",
                session_id="m2-child-a",
                tool_call_id="m2-a-ok",
            )
            handle_function_call(
                "terminal",
                {"command": "python -c \"import sys; sys.exit(3)\""},
                task_id="m2-task-b",
                session_id="m2-child-b",
                tool_call_id="m2-b-fail",
            )
            handle_function_call(
                "terminal",
                {"command": "python -c \"print('repair recovered')\""},
                task_id="m2-task-b",
                session_id="m2-child-b",
                tool_call_id="m2-b-ok",
            )

            invoke_hook(
                "on_session_end",
                session_id="m2-parent-session",
                task_id="m2-task",
                turn_id="m2-parent-turn",
                completed=True,
                failed=False,
                interrupted=False,
                model="test-model",
                platform="cli",
            )

            from adaptive_evolution_observer.cli import status

            report = status(db)
            state = report["state"]
            diagnostics = report["events"]
            expected = {
                "schema": "adaptive-evolution.organization-state.v0.4",
                "agents": 3,
                "interaction_events": 2,
                "completed_interaction_events": 2,
                "interaction_completion_coverage": 1.0,
                "directed_traffic_breadth": 1.0,
                "completed_flow_connectivity": 1.0 / 3.0,
                "uncertain_session_events": 0,
            }

            failures = []
            for key in ("schema", "agents", "interaction_events", "completed_interaction_events"):
                if state.get(key) != expected[key]:
                    failures.append(f"{key}: {state.get(key)!r} != {expected[key]!r}")
            for key in (
                "interaction_completion_coverage",
                "directed_traffic_breadth",
                "completed_flow_connectivity",
            ):
                value = state.get(key)
                if value is None or abs(float(value) - float(expected[key])) > 1e-9:
                    failures.append(f"{key}: {value!r} != {expected[key]!r}")
            if int(diagnostics.get("uncertain_session_events") or 0) != 0:
                failures.append(f"uncertain identity: {diagnostics}")
            if state.get("directed_diffusivity_authority") != "deprecated_diagnostic_only":
                failures.append("legacy directed_diffusivity regained authority")
            if failures:
                raise SystemExit("M2 offline multi-edge contract failed: " + "; ".join(failures))

            result = {
                "schema": "adaptive-evolution.m2-offline-multiedge-contract.v0.1",
                "result": "compatible",
                "expected": expected,
                "event_diagnostics": diagnostics,
                "organization_state": state,
                "authority": "offline_real_hermes_contract_only",
                "note": (
                    "The delegation lifecycle is real Hermes code; child LLM execution is mocked. "
                    "This validates v0.4 observability semantics, not routing usefulness."
                ),
            }
            out = os.getenv("ADAPTIVE_EVOLUTION_M2_OFFLINE_RESULT")
            if out:
                target = Path(out)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        finally:
            plugins._plugin_manager = original_manager


if __name__ == "__main__":
    raise SystemExit(main())

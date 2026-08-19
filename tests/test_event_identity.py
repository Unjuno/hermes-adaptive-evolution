from __future__ import annotations

from adaptive_evolution_observer.normalizer import normalize
from adaptive_evolution_observer.store import event_key


def _row(hook, payload, received_at_ns):
    return {
        "received_at_ns": received_at_ns,
        "hook": hook,
        "event_key": event_key(hook, payload),
        "payload": payload,
    }


def test_api_retries_with_same_request_id_are_distinct_events():
    first = {
        "session_id": "s1",
        "turn_id": "t1",
        "api_request_id": "api-1",
        "retry_count": 0,
        "max_retries": 2,
        "status_code": 500,
    }
    second = dict(first, retry_count=1)
    assert event_key("api_request_error", first) != event_key("api_request_error", second)

    events, diag = normalize([
        _row("api_request_error", first, 1),
        _row("api_request_error", second, 2),
    ])
    assert len(events) == 2
    assert diag["duplicates_removed"] == 0


def test_exact_api_retry_duplicate_is_removed():
    payload = {
        "session_id": "s1",
        "turn_id": "t1",
        "api_request_id": "api-1",
        "retry_count": 1,
        "max_retries": 2,
        "status_code": 500,
    }
    row = _row("api_request_error", payload, 1)
    events, diag = normalize([row, dict(row, received_at_ns=2)])
    assert len(events) == 1
    assert diag["duplicates_removed"] == 1


def test_skill_use_count_prevents_false_dedup():
    first = {
        "session_id": "s1",
        "task_id": "task-1",
        "action": "used",
        "skill_name": "repair",
        "use_count": 1,
        "reused": False,
        "reuse_after_patch": False,
        "provenance": "plugin",
    }
    second = dict(first, use_count=2, reused=True)
    assert event_key("on_skill_lifecycle", first) != event_key("on_skill_lifecycle", second)

    events, diag = normalize([
        _row("on_skill_lifecycle", first, 1),
        _row("on_skill_lifecycle", second, 2),
    ])
    assert len(events) == 2
    assert diag["duplicates_removed"] == 0


def test_session_reset_ids_participate_in_event_identity():
    first = {"session_id": "s1", "old_session_id": "s1", "new_session_id": "s2"}
    second = {"session_id": "s1", "old_session_id": "s2", "new_session_id": "s3"}
    assert event_key("on_session_reset", first) != event_key("on_session_reset", second)

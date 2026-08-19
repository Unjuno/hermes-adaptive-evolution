from __future__ import annotations

import threading
from pathlib import Path

from adaptive_evolution_observer.store import EventStore


def test_concurrent_hook_writes_are_not_lost(tmp_path: Path):
    store = EventStore(tmp_path / "observer.sqlite3")
    threads = []
    workers = 8
    writes_per_worker = 40

    def writer(worker: int):
        for i in range(writes_per_worker):
            store.append(
                "post_tool_call",
                {
                    "session_id": f"session-{worker}",
                    "turn_id": f"turn-{i}",
                    "tool_call_id": f"tool-{worker}-{i}",
                    "tool_name": "python",
                    "status": "success",
                },
            )

    for worker in range(workers):
        thread = threading.Thread(target=writer, args=(worker,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()

    expected = workers * writes_per_worker
    assert store.count() == expected
    rows = store.load()
    assert len(rows) == expected
    assert len({row["payload"]["tool_call_id"] for row in rows}) == expected

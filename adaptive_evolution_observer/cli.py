from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .estimator import estimate
from .normalizer import normalize
from .store import EventStore


def status(db: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    store = EventStore(db)
    canonical, diagnostics = normalize(store.load(limit=limit))
    return {
        "database": str(store.path),
        "events": diagnostics,
        "state": estimate(canonical),
    }


def export(db: str | Path | None, path: str | Path) -> dict[str, Any]:
    store = EventStore(db)
    canonical, diagnostics = normalize(store.load())
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for e in canonical:
            f.write(json.dumps({
                "seq": e.seq,
                "hook": e.hook,
                "event_key": e.event_key,
                "session_id": e.session_id,
                "task_id": e.task_id,
                "turn_id": e.turn_id,
                "agent_id": e.agent_id,
                "parent_agent_id": e.parent_agent_id,
                "kind": e.kind,
                "data": e.data,
            }, ensure_ascii=False, sort_keys=True) + "\n")
    return {"database": str(store.path), "path": str(target), "events": diagnostics}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adaptive-evolution-observer")
    parser.add_argument("--db", help="Observer SQLite path. Uses the plugin default when omitted.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Print normalized diagnostics and organization state as JSON.")
    p_status.add_argument("--limit", type=int, default=None, help="Analyze only the most recent N events.")

    p_export = sub.add_parser("export", help="Export normalized/deduplicated events as JSONL.")
    p_export.add_argument("path", help="Destination JSONL path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        if args.limit is not None and args.limit < 1:
            raise SystemExit("--limit must be >= 1")
        result = status(args.db, args.limit)
    else:
        result = export(args.db, args.path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

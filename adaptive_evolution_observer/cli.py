from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .bundle import create_bundle, replay_bundle
from .estimator import estimate
from .normalizer import normalize
from .store import EventStore
from .window import select_recent


def status(db: str | Path | None = None, limit: int | None = None) -> dict[str, Any]:
    store = EventStore(db)
    canonical, diagnostics = normalize(store.load())
    selected, window = select_recent(canonical, limit)
    return {
        "database": str(store.path),
        "events": diagnostics,
        "window": window,
        "state": estimate(selected),
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
                "observed_at_ns": e.observed_at_ns,
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
    parser.add_argument("--db", help="Observer SQLite path. Uses the active Hermes profile default when omitted.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Print normalized diagnostics and organization state as JSON.")
    p_status.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Estimate state on the most recent N normalized events while preserving full-history identity context.",
    )

    p_export = sub.add_parser("export", help="Export normalized/deduplicated events as JSONL.")
    p_export.add_argument("path", help="Destination JSONL path.")

    p_bundle = sub.add_parser("bundle", help="Create a checksummed, metadata-first portable capture bundle.")
    p_bundle.add_argument("directory", help="Destination directory for manifest and sanitized/normalized event streams.")

    p_replay = sub.add_parser("replay", help="Verify and replay a portable capture bundle without SQLite.")
    p_replay.add_argument("directory", help="Capture bundle directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        if args.limit is not None and args.limit < 1:
            raise SystemExit("--limit must be >= 1")
        result = status(args.db, args.limit)
    elif args.command == "export":
        result = export(args.db, args.path)
    elif args.command == "bundle":
        result = create_bundle(args.db, args.directory)
    else:
        result = replay_bundle(args.directory)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

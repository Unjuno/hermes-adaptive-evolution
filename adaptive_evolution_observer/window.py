from __future__ import annotations

from typing import Any

from .normalizer import CanonicalEvent


def select_recent(
    events: list[CanonicalEvent], limit: int | None
) -> tuple[list[CanonicalEvent], dict[str, Any]]:
    """Select a recent measurement window after full-history normalization.

    Identity/correlation must be resolved with the complete available event
    history first. Applying a SQL tail limit before normalization can discard a
    previous ``subagent_start`` edge and incorrectly turn a known child into an
    uncertain session. This helper deliberately windows canonical events only.
    """
    total = len(events)
    if limit is None:
        return events, {
            "requested_limit": None,
            "context_events": total,
            "selected_events": total,
            "identity_context_preserved": True,
        }
    limit = max(1, int(limit))
    selected = events[-limit:]
    return selected, {
        "requested_limit": limit,
        "context_events": total,
        "selected_events": len(selected),
        "identity_context_preserved": True,
    }

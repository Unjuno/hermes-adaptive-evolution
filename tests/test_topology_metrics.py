from __future__ import annotations

import numpy as np

from adaptive_evolution_observer.estimator import (
    interaction_branching_entropy,
    interaction_reciprocity,
    recurrent_core_fraction,
    recurrent_core_mixing_gap,
)


def _counts(n: int, edges: list[tuple[int, int]]) -> np.ndarray:
    out = np.zeros((n, n), dtype=float)
    for i, j in edges:
        out[i, j] += 1.0
    return out


def test_acyclic_delegation_does_not_invent_recurrent_gap():
    star = _counts(5, [(0, 1), (0, 2), (0, 3), (0, 4)])
    chain = _counts(5, [(0, 1), (1, 2), (2, 3), (3, 4)])

    assert recurrent_core_fraction(star) == 0.0
    assert recurrent_core_fraction(chain) == 0.0
    assert recurrent_core_mixing_gap(star) is None
    assert recurrent_core_mixing_gap(chain) is None
    assert interaction_branching_entropy(star) > interaction_branching_entropy(chain)


def test_reciprocity_is_distinct_from_recurrence():
    cycle = _counts(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    ring = _counts(
        5,
        [(i, (i + 1) % 5) for i in range(5)]
        + [(i, (i - 1) % 5) for i in range(5)],
    )

    assert recurrent_core_fraction(cycle) == 1.0
    assert recurrent_core_fraction(ring) == 1.0
    assert interaction_reciprocity(cycle) == 0.0
    assert interaction_reciprocity(ring) == 1.0
    assert recurrent_core_mixing_gap(cycle) is not None
    assert recurrent_core_mixing_gap(ring) is not None


def test_dense_recurrent_traffic_has_high_branching_and_reciprocity():
    complete = _counts(5, [(i, j) for i in range(5) for j in range(5) if i != j])

    assert interaction_branching_entropy(complete) == 1.0
    assert interaction_reciprocity(complete) == 1.0
    assert recurrent_core_fraction(complete) == 1.0
    gap = recurrent_core_mixing_gap(complete)
    assert gap is not None
    assert gap > 0.5

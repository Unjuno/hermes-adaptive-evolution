from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import deque

A = "A"
B = "B"


def reward_mean(rule: str, t: int, shift_t: int, rare: bool) -> float:
    correct = A if t < shift_t else B
    if rule == correct:
        return 0.72 if rare else 0.68
    # Stale/reward-hacking rule remains superficially attractive in common contexts.
    return 0.08 if rare else 0.56


class Curator:
    def __init__(self, mode: str, window: int = 150, decay: float = 0.985,
                 rare_weight: float = 8.0, patience: int = 3) -> None:
        self.mode = mode
        self.window = window
        self.decay = decay
        self.rare_weight = rare_weight
        self.patience = patience
        self.evidence = deque()
        self.sums = {A: 0.0, B: 0.0}
        self.weights = {A: 0.0, B: 0.0}
        self.bad_streak = 0
        self.last_recommendation: str | None = None

    def recommendation(self) -> str:
        ma = self.sums[A] / self.weights[A] if self.weights[A] else -1e9
        mb = self.sums[B] / self.weights[B] if self.weights[B] else -1e9
        return A if ma >= mb else B

    def add(self, t: int, rule: str, reward: float, rare: bool) -> None:
        if self.mode == "exp_decay":
            for candidate in (A, B):
                self.sums[candidate] *= self.decay
                self.weights[candidate] *= self.decay

        weight = self.rare_weight if rare else 1.0
        self.evidence.append((t, rule, reward, rare, weight))
        self.sums[rule] += weight * reward
        self.weights[rule] += weight

        if self.mode in {"window", "changepoint"}:
            while self.evidence and self.evidence[0][0] < t - self.window:
                _, old_rule, old_reward, _, old_weight = self.evidence.popleft()
                self.sums[old_rule] -= old_weight * old_reward
                self.weights[old_rule] -= old_weight

        if self.mode == "changepoint":
            current = self.recommendation()
            if self.last_recommendation is None:
                self.last_recommendation = current
            if rare and rule == self.last_recommendation and reward < 0.25:
                self.bad_streak += 1
            elif rare and rule == self.last_recommendation and reward > 0.50:
                self.bad_streak = max(0, self.bad_streak - 1)

            if self.bad_streak >= self.patience:
                # Forget aggressively when independent rare-context evidence repeatedly
                # contradicts the current institutional recommendation.
                self.evidence.clear()
                self.sums = {A: 0.0, B: 0.0}
                self.weights = {A: 0.0, B: 0.0}
                self.bad_streak = 0
                self.last_recommendation = None


def run(seed: int, mode: str, federated: int = 1, steps: int = 300,
        shift_t: int = 150, n_agents: int = 50) -> dict:
    rng = random.Random(seed)
    agents = [rng.choice((A, B)) for _ in range(n_agents)]
    scores = [{A: 0.0, B: 0.0} for _ in range(n_agents)]
    counts = [{A: 0, B: 0} for _ in range(n_agents)]

    def observe(i: int, rule: str, reward: float) -> None:
        counts[i][rule] += 1
        alpha = min(0.25, 1.0 / math.sqrt(counts[i][rule]))
        scores[i][rule] = (1.0 - alpha) * scores[i][rule] + alpha * reward

    curators: list[Curator] = []
    if mode != "peer":
        for _ in range(federated):
            if mode == "long":
                curators.append(Curator("window", window=9999))
            elif mode == "window":
                curators.append(Curator("window", window=60))
            elif mode == "exp_decay":
                curators.append(Curator("exp_decay", decay=0.985))
            elif mode == "changepoint":
                curators.append(Curator("changepoint", window=150, patience=3))
            else:
                raise ValueError(mode)

    history: list[float] = []

    for t in range(steps):
        for i, rule in enumerate(agents):
            rare = rng.random() < 0.08
            reward = max(0.0, min(1.0, rng.gauss(reward_mean(rule, t, shift_t, rare), 0.12)))
            observe(i, rule, reward)
            for curator in curators:
                curator.add(t, rule, reward, rare)

        # Independent verification deliberately samples the rare/counterfactual regime.
        for i, rule in enumerate(agents):
            if rng.random() < 0.10:
                reward = max(0.0, min(1.0, rng.gauss(reward_mean(rule, t, shift_t, True), 0.12)))
                observe(i, rule, reward)
                for curator in curators:
                    curator.add(t, rule, reward, True)

        # Random propagation: social transmission, not truth estimation.
        for _ in range(max(1, int(n_agents * 0.25))):
            source, target = rng.sample(range(n_agents), 2)
            observe(target, agents[source], 0.59)

        if curators and t > 0 and t % 12 == 0:
            recommendations = [c.recommendation() for c in curators]
            recommendation = A if recommendations.count(A) > recommendations.count(B) else B
            for i in range(n_agents):
                if rng.random() < 0.45:
                    observe(i, recommendation, 0.76)

        for i in range(n_agents):
            sa = scores[i][A] if counts[i][A] else -1e9
            sb = scores[i][B] if counts[i][B] else -1e9
            agents[i] = rng.choice((A, B)) if abs(sa - sb) < 1e-12 else (A if sa > sb else B)

        correct = A if t < shift_t else B
        history.append(sum(rule == correct for rule in agents) / n_agents)

    latency = None
    for t in range(shift_t, steps - 9):
        if min(history[t:t + 10]) >= 0.70:
            latency = t - shift_t
            break

    return {
        "pre_shift_accuracy": statistics.mean(history[shift_t - 40:shift_t]),
        "post_shift_accuracy_last40": statistics.mean(history[-40:]),
        "adaptation_latency": latency,
        "failed_to_adapt": latency is None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=300)
    args = parser.parse_args()

    variants = [
        ("peer", "peer", 1),
        ("long_archive", "long", 1),
        ("short_window", "window", 1),
        ("exponential_decay", "exp_decay", 1),
        ("changepoint", "changepoint", 1),
        ("changepoint_federated5", "changepoint", 5),
    ]

    summary = {}
    for name, mode, federated in variants:
        rows = [run(seed, mode, federated=federated) for seed in range(args.seeds)]
        latencies = [row["adaptation_latency"] if row["adaptation_latency"] is not None else 151 for row in rows]
        summary[name] = {
            "pre_shift_accuracy_mean": statistics.mean(r["pre_shift_accuracy"] for r in rows),
            "post_shift_accuracy_last40_mean": statistics.mean(r["post_shift_accuracy_last40"] for r in rows),
            "adaptation_latency_median": statistics.median(latencies),
            "failed_to_adapt_rate": statistics.mean(r["failed_to_adapt"] for r in rows),
        }

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

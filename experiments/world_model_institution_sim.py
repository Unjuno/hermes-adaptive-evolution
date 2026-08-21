from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import deque
from dataclasses import dataclass, field

TRUE = "T"
HACK = "H"


@dataclass
class Config:
    n_agents: int = 60
    steps: int = 240
    delay: int = 8
    rare_context_prob: float = 0.08
    local_verify_prob: float = 0.10
    transmission_rate: float = 0.25
    mutation_rate: float = 0.01
    broadcast_interval: int = 12
    memory_window: int = 120
    curator_count: int = 1
    curator_tenure: int = 240
    authority_weight: float = 0.70
    capture_prob: float = 0.0
    reward_noise: float = 0.12
    rare_weight: float = 1.0


def mean_reward(rule: str, rare: bool) -> float:
    """Toy environment: H looks good in common contexts but fails counterfactual tests."""
    if rule == TRUE:
        return 0.68 if not rare else 0.72
    return 0.84 if not rare else 0.05


@dataclass
class Pending:
    due: int
    agent: int
    rule: str
    rare: bool
    reward: float


@dataclass
class Agent:
    rule: str
    score: dict[str, float] = field(default_factory=lambda: {TRUE: 0.0, HACK: 0.0})
    count: dict[str, int] = field(default_factory=lambda: {TRUE: 0, HACK: 0})

    def observe(self, rule: str, reward: float) -> None:
        self.count[rule] += 1
        n = self.count[rule]
        alpha = min(0.25, 1.0 / math.sqrt(n))
        self.score[rule] = (1.0 - alpha) * self.score[rule] + alpha * reward

    def choose(self, rng: random.Random) -> str:
        if self.count[TRUE] == 0 and self.count[HACK] == 0:
            return self.rule
        st = self.score[TRUE] if self.count[TRUE] else -1e9
        sh = self.score[HACK] if self.count[HACK] else -1e9
        if abs(st - sh) < 1e-12:
            return rng.choice([TRUE, HACK])
        return TRUE if st > sh else HACK


@dataclass
class Curator:
    window: int
    captured: bool = False
    rare_weight: float = 1.0
    evidence: deque = field(default_factory=deque)
    sums: dict[str, float] = field(default_factory=lambda: {TRUE: 0.0, HACK: 0.0})
    counts: dict[str, float] = field(default_factory=lambda: {TRUE: 0.0, HACK: 0.0})

    def add(self, t: int, rule: str, reward: float, rare: bool) -> None:
        self.evidence.append((t, rule, reward, rare))
        weight = self.rare_weight if rare else 1.0
        self.sums[rule] += weight * reward
        self.counts[rule] += weight
        while self.evidence and self.evidence[0][0] < t - self.window:
            _, old_rule, old_reward, old_rare = self.evidence.popleft()
            old_weight = self.rare_weight if old_rare else 1.0
            self.sums[old_rule] -= old_weight * old_reward
            self.counts[old_rule] -= old_weight

    def recommendation(self) -> str:
        if self.captured:
            return HACK
        means = {
            rule: (self.sums[rule] / self.counts[rule] if self.counts[rule] else -1e9)
            for rule in [TRUE, HACK]
        }
        return TRUE if means[TRUE] >= means[HACK] else HACK


def new_curators(cfg: Config, rng: random.Random) -> list[Curator]:
    return [
        Curator(
            window=cfg.memory_window,
            captured=rng.random() < cfg.capture_prob,
            rare_weight=cfg.rare_weight,
        )
        for _ in range(cfg.curator_count)
    ]


def run(seed: int, mode: str, cfg: Config) -> dict[str, float | bool]:
    rng = random.Random(seed)
    agents = [
        Agent(rule=TRUE if i == 0 else HACK if i == 1 else rng.choice([TRUE, HACK]))
        for i in range(cfg.n_agents)
    ]
    pending: list[Pending] = []
    curators = [] if mode == "peer" else new_curators(cfg, rng)
    true_history: list[float] = []
    takeover = False

    for t in range(cfg.steps):
        arriving = [item for item in pending if item.due == t]
        if arriving:
            for item in arriving:
                agents[item.agent].observe(item.rule, item.reward)
                for curator in curators:
                    curator.add(t, item.rule, item.reward, item.rare)
            pending = [item for item in pending if item.due != t]

        for i, agent in enumerate(agents):
            rare = rng.random() < cfg.rare_context_prob
            reward = max(
                0.0,
                min(1.0, rng.gauss(mean_reward(agent.rule, rare), cfg.reward_noise)),
            )
            pending.append(Pending(t + cfg.delay, i, agent.rule, rare, reward))

        # Independent local verification: deliberately samples the rare/counterfactual context.
        for agent in agents:
            if rng.random() < cfg.local_verify_prob:
                reward = max(
                    0.0,
                    min(1.0, rng.gauss(mean_reward(agent.rule, True), cfg.reward_noise)),
                )
                agent.observe(agent.rule, reward)
                for curator in curators:
                    curator.add(t, agent.rule, reward, True)

        # Random social transmission. This is propagation, not truth estimation.
        contacts = max(1, int(cfg.n_agents * cfg.transmission_rate))
        for _ in range(contacts):
            source, target = rng.sample(range(cfg.n_agents), 2)
            proposed = agents[source].rule
            agents[target].observe(proposed, 0.55 if proposed == TRUE else 0.60)

        # Institution/curator broadcast. A long-lived curator is an archetype, not a claim
        # that any historical political system is globally optimal.
        if curators and t > 0 and t % cfg.broadcast_interval == 0:
            recommendations = [curator.recommendation() for curator in curators]
            recommendation = TRUE if recommendations.count(TRUE) > recommendations.count(HACK) else HACK
            for agent in agents:
                if rng.random() < cfg.authority_weight:
                    agent.observe(recommendation, 0.75)

        # Rotating institutions lose accumulated evidence at tenure boundaries.
        if (
            curators
            and cfg.curator_tenure < cfg.steps
            and t > 0
            and t % cfg.curator_tenure == 0
        ):
            curators = new_curators(cfg, rng)

        for agent in agents:
            if rng.random() < cfg.mutation_rate:
                agent.rule = TRUE if agent.rule == HACK else HACK
            else:
                agent.rule = agent.choose(rng)

        true_fraction = sum(agent.rule == TRUE for agent in agents) / cfg.n_agents
        true_history.append(true_fraction)
        takeover = takeover or (1.0 - true_fraction > 0.80)

    return {
        "final_true": true_history[-1],
        "mean_true_last50": statistics.mean(true_history[-50:]),
        "hack_takeover": takeover,
    }


def variants() -> dict[str, tuple[str, Config]]:
    return {
        "peer": ("peer", Config()),
        "long_memory_raw_feedback": (
            "curated",
            Config(memory_window=180, curator_count=1, curator_tenure=240, authority_weight=0.70),
        ),
        "rotating_short_memory": (
            "curated",
            Config(memory_window=36, curator_count=1, curator_tenure=36, authority_weight=0.70),
        ),
        "federated_5": (
            "curated",
            Config(memory_window=120, curator_count=5, curator_tenure=240, authority_weight=0.45),
        ),
        "long_archive_context_balanced": (
            "curated",
            Config(
                memory_window=180,
                curator_count=1,
                curator_tenure=240,
                authority_weight=0.55,
                rare_weight=8.0,
            ),
        ),
        "rotating_archive_context_balanced": (
            "curated",
            Config(
                memory_window=36,
                curator_count=1,
                curator_tenure=36,
                authority_weight=0.55,
                rare_weight=8.0,
            ),
        ),
        "federated_archive_context_balanced": (
            "curated",
            Config(
                memory_window=120,
                curator_count=5,
                curator_tenure=240,
                authority_weight=0.35,
                rare_weight=8.0,
            ),
        ),
        "captured_long_archive_5pct": (
            "curated",
            Config(
                memory_window=180,
                curator_count=1,
                curator_tenure=240,
                authority_weight=0.55,
                rare_weight=8.0,
                capture_prob=0.05,
            ),
        ),
        "captured_federated_archive_5pct": (
            "curated",
            Config(
                memory_window=120,
                curator_count=5,
                curator_tenure=240,
                authority_weight=0.35,
                rare_weight=8.0,
                capture_prob=0.05,
            ),
        ),
    }


def sweep(seeds: int) -> dict[str, dict[str, float | int]]:
    output: dict[str, dict[str, float | int]] = {}
    for name, (mode, cfg) in variants().items():
        records = [run(seed, mode, cfg) for seed in range(seeds)]
        last50 = [float(record["mean_true_last50"]) for record in records]
        output[name] = {
            "n": seeds,
            "mean_true_last50": statistics.mean(last50),
            "median_true_last50": statistics.median(last50),
            "hack_takeover_rate": sum(bool(record["hack_takeover"]) for record in records) / seeds,
            "final_true_mean": statistics.mean(float(record["final_true"]) for record in records),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()
    result = sweep(args.seeds)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()

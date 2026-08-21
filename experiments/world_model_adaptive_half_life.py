from __future__ import annotations

import argparse
import json
import random
import statistics

A = "A"
B = "B"


def run(seed: int, mode: str = "fixed", steps: int = 360, shift_t: int = 180,
        n_agents: int = 50, verify_prob: float = 0.12,
        rare_prob: float = 0.08, transmission_rate: float = 0.25,
        base_half_life: float = 60.0, min_half_life: float = 6.0,
        max_half_life: float = 240.0, diversity_gain: float = 0.10,
        contradiction_penalty: float = 0.35) -> dict:
    rng = random.Random(seed)
    rules = (A, B)

    agents = [
        {
            "rule": rules[i % 2],
            "score": {A: 1.0, B: 1.0},
            "half_life": {A: base_half_life, B: base_half_life},
            "verified": {A: 0, B: 0},
        }
        for i in range(n_agents)
    ]

    def true_rule(t: int) -> str:
        return A if t < shift_t else B

    def reward(rule: str, t: int, rare: bool) -> float:
        if rule == true_rule(t):
            mu = 0.72 if rare else 0.68
        else:
            # A stale / reward-hacking rule is still superficially attractive
            # in common contexts, but fails rare/counterfactual tests.
            mu = 0.08 if rare else 0.56
        return min(1.0, max(0.0, rng.gauss(mu, 0.12)))

    history: list[float] = []

    for t in range(steps):
        # Knowledge-specific forgetting.
        for agent in agents:
            for rule in rules:
                half_life = (
                    agent["half_life"][rule]
                    if mode == "adaptive"
                    else base_half_life
                )
                agent["score"][rule] *= 0.5 ** (1.0 / max(half_life, 1e-9))

        for agent in agents:
            rule = agent["rule"]
            rare = rng.random() < rare_prob
            observed = reward(rule, t, rare)
            agent["score"][rule] += observed

            if rare and mode == "adaptive":
                if observed >= 0.5:
                    agent["verified"][rule] += 1
                    n = agent["verified"][rule]
                    agent["half_life"][rule] = min(
                        max_half_life,
                        agent["half_life"][rule]
                        * (1.0 + diversity_gain / (1.0 + 0.1 * n)),
                    )
                elif observed < 0.25:
                    agent["half_life"][rule] = max(
                        min_half_life,
                        agent["half_life"][rule] * contradiction_penalty,
                    )

            # Independent verifier probes both candidate rules in a rare context.
            # This is intentionally separated from propagation.
            if rng.random() < verify_prob:
                for candidate in rules:
                    verified_reward = reward(candidate, t, True)
                    agent["score"][candidate] += 2.5 * verified_reward
                    if mode == "adaptive":
                        if verified_reward >= 0.5:
                            agent["verified"][candidate] += 1
                            n = agent["verified"][candidate]
                            agent["half_life"][candidate] = min(
                                max_half_life,
                                agent["half_life"][candidate]
                                * (1.0 + diversity_gain / (1.0 + 0.1 * n)),
                            )
                        elif verified_reward < 0.25:
                            agent["half_life"][candidate] = max(
                                min_half_life,
                                agent["half_life"][candidate]
                                * contradiction_penalty,
                            )

        # Random social transmission is weak evidence only.
        contacts = max(1, int(n_agents * transmission_rate))
        for _ in range(contacts):
            source, target = rng.sample(range(n_agents), 2)
            proposed = agents[source]["rule"]
            agents[target]["score"][proposed] += 0.20

        for agent in agents:
            agent["rule"] = A if agent["score"][A] >= agent["score"][B] else B

        correct_fraction = (
            sum(agent["rule"] == true_rule(t) for agent in agents) / n_agents
        )
        history.append(correct_fraction)

    adaptation_delay = None
    for t in range(shift_t, steps - 9):
        if min(history[t:t + 10]) >= 0.80:
            adaptation_delay = t - shift_t
            break

    return {
        "seed": seed,
        "mode": mode,
        "final_correct": statistics.mean(history[-50:]),
        "adaptation_delay": (
            adaptation_delay if adaptation_delay is not None else steps - shift_t
        ),
        "adaptation_failed": adaptation_delay is None,
        "median_stale_half_life": statistics.median(
            agent["half_life"][A] for agent in agents
        ),
        "median_current_half_life": statistics.median(
            agent["half_life"][B] for agent in agents
        ),
    }


def summarize(rows: list[dict]) -> dict:
    by_mode: dict[str, list[dict]] = {}
    for row in rows:
        by_mode.setdefault(row["mode"], []).append(row)

    out = {}
    for mode, subset in by_mode.items():
        out[mode] = {
            "n": len(subset),
            "final_correct_mean": statistics.mean(r["final_correct"] for r in subset),
            "adaptation_delay_median": statistics.median(r["adaptation_delay"] for r in subset),
            "adaptation_delay_mean": statistics.mean(r["adaptation_delay"] for r in subset),
            "adaptation_failure_rate": statistics.mean(float(r["adaptation_failed"]) for r in subset),
            "median_stale_half_life": statistics.median(r["median_stale_half_life"] for r in subset),
            "median_current_half_life": statistics.median(r["median_current_half_life"] for r in subset),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = []
    for mode in ("fixed", "adaptive"):
        for seed in range(args.seeds):
            rows.append(run(seed, mode=mode))

    result = {
        "schema": "adaptive-evolution.world-model-adaptive-half-life.v0.1",
        "summary": summarize(rows),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for mode, stats in result["summary"].items():
            print(mode, stats)


if __name__ == "__main__":
    main()

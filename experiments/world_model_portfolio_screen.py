from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics


def run(seed: int, propagation: str, verify_domains: int, memory: str,
        exploration: str, phase: str, n_agents: int = 24,
        steps: int = 160, shift_t: int = 80) -> dict:
    rng = random.Random(seed)
    agents = [[rng.random(), 1.0, 40.0, 0] for _ in range(n_agents)]
    history = []
    takeover = False
    verify_phases = 0
    domain_bad = [False] * verify_domains
    domain_ttl = [0] * verify_domains

    for t in range(steps):
        optimum = 0.25 if t < shift_t else 0.75

        for agent in agents:
            half_life = agent[2] if memory == "adaptive" else 40.0
            agent[1] *= 0.5 ** (1.0 / half_life)

            base = max(0.0, 1.0 - 1.8 * abs(agent[0] - optimum))
            shortcut = 0.18 * math.exp(-((agent[0] - 0.5) / 0.09) ** 2)
            reward = min(1.0, max(0.0, base + shortcut + rng.gauss(0.0, 0.06)))
            agent[1] += 0.15 * (reward - 0.5)

            if memory == "adaptive":
                if reward < 0.25:
                    agent[2] = max(5.0, agent[2] * 0.80)
                elif reward > 0.70:
                    agent[2] = min(160.0, agent[2] * 1.015)

        if phase == "fixed":
            do_verify = t % 4 == 3
        else:
            xs = [agent[0] for agent in agents]
            mean_x = sum(xs) / n_agents
            disagreement = (
                sum((x - mean_x) ** 2 for x in xs) / n_agents
            ) ** 0.5
            contradiction = sum(agent[3] for agent in agents) / n_agents
            do_verify = (
                disagreement > 0.30
                or contradiction > 1.5
                or t % 12 == 11
            )

        if do_verify:
            verify_phases += 1
            for domain in range(verify_domains):
                if domain_ttl[domain] > 0:
                    domain_ttl[domain] -= 1
                elif rng.random() < 0.05:
                    domain_bad[domain] = True
                    domain_ttl[domain] = rng.randint(2, 5)
                else:
                    domain_bad[domain] = False

            for agent in agents:
                domain = rng.randrange(verify_domains)
                verified_reward = min(
                    1.0,
                    max(
                        0.0,
                        1.0 - 2.8 * abs(agent[0] - optimum)
                        + rng.gauss(0.0, 0.05),
                    ),
                )
                if domain_bad[domain]:
                    verified_reward = 1.0 - verified_reward

                agent[1] += 0.5 * (verified_reward - 0.5)
                if verified_reward < 0.25:
                    agent[3] += 1
                    if memory == "adaptive":
                        agent[2] = max(5.0, agent[2] * 0.45)
                elif verified_reward > 0.70:
                    agent[3] = max(0, agent[3] - 1)
                    if memory == "adaptive":
                        agent[2] = min(160.0, agent[2] * 1.04)

        for agent in agents:
            if exploration == "constant":
                probability = 0.025
                sigma = 0.08
            else:
                probability = min(0.25, 0.008 + 0.06 * agent[3])
                sigma = min(0.22, 0.06 + 0.025 * agent[3])

            if rng.random() < probability:
                agent[0] = min(1.0, max(0.0, rng.gauss(agent[0], sigma)))
                agent[1] *= 0.70
                agent[3] = max(0, agent[3] - 1)

        if not do_verify:
            rate = 0.12 if propagation == "low" else 0.55
            contacts = max(1, int(n_agents * rate))
            for _ in range(contacts):
                source, target = rng.sample(range(n_agents), 2)
                src, dst = agents[source], agents[target]
                p_copy = 1.0 / (1.0 + math.exp(-(src[1] - dst[1])))
                if rng.random() < p_copy:
                    dst[0] = 0.65 * dst[0] + 0.35 * src[0]
                    dst[1] = 0.80 * dst[1] + 0.20 * src[1]

        good = sum(abs(agent[0] - optimum) < 0.12 for agent in agents) / n_agents
        hack = sum(abs(agent[0] - 0.5) < 0.10 for agent in agents) / n_agents
        history.append((good, hack))
        takeover = takeover or hack > 0.60

    adaptation_delay = steps - shift_t
    for t in range(shift_t, steps - 7):
        if min(good for good, _ in history[t:t + 8]) >= 0.65:
            adaptation_delay = t - shift_t
            break

    return {
        "final_good": statistics.mean(good for good, _ in history[-20:]),
        "final_hack": statistics.mean(hack for _, hack in history[-20:]),
        "adaptation_delay": adaptation_delay,
        "hack_takeover": float(takeover),
        "verification_phases": verify_phases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = []
    grid = itertools.product(
        ("low", "high"),
        (1, 8),
        ("fixed", "adaptive"),
        ("constant", "triggered"),
        ("fixed", "adaptive"),
    )

    for propagation, verify_domains, memory, exploration, phase in grid:
        trials = [
            run(seed, propagation, verify_domains, memory, exploration, phase)
            for seed in range(args.seeds)
        ]
        rows.append({
            "propagation": propagation,
            "verify_domains": verify_domains,
            "memory": memory,
            "exploration": exploration,
            "phase": phase,
            "n": len(trials),
            "final_good_mean": statistics.mean(t["final_good"] for t in trials),
            "final_hack_mean": statistics.mean(t["final_hack"] for t in trials),
            "adaptation_delay_median": statistics.median(
                t["adaptation_delay"] for t in trials
            ),
            "hack_takeover_rate": statistics.mean(
                t["hack_takeover"] for t in trials
            ),
            "verification_phases_mean": statistics.mean(
                t["verification_phases"] for t in trials
            ),
        })

    def marginal(field: str) -> dict:
        values = sorted({row[field] for row in rows}, key=str)
        out = {}
        for value in values:
            subset = [row for row in rows if row[field] == value]
            out[str(value)] = {
                "final_good_mean": statistics.mean(r["final_good_mean"] for r in subset),
                "final_hack_mean": statistics.mean(r["final_hack_mean"] for r in subset),
                "hack_takeover_rate": statistics.mean(r["hack_takeover_rate"] for r in subset),
                "verification_phases_mean": statistics.mean(
                    r["verification_phases_mean"] for r in subset
                ),
            }
        return out

    result = {
        "schema": "adaptive-evolution.world-model-portfolio-screen.v0.1",
        "seeds_per_cell": args.seeds,
        "cells": rows,
        "marginals": {
            field: marginal(field)
            for field in (
                "propagation",
                "verify_domains",
                "memory",
                "exploration",
                "phase",
            )
        },
        "warning": (
            "Diagnostic factorial screen only. Main effects are descriptive and may "
            "contain interactions; no production or LLM-level conclusion follows."
        ),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        ranked = sorted(
            rows,
            key=lambda row: (-row["final_good_mean"], row["hack_takeover_rate"]),
        )
        for row in ranked[:10]:
            print(row)
        print("marginals=", json.dumps(result["marginals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

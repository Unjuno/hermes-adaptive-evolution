from __future__ import annotations

import argparse
import json
import random
import statistics

MODES = ("random", "push", "pull", "negotiated")


def run(seed: int, mode: str, steps: int = 220, n_agents: int = 36, shift_t: int = 110) -> dict:
    rng = random.Random(seed)
    n_types = 3
    capabilities = [[rng.random() for _ in range(n_types)] for _ in range(n_agents)]
    sender_estimate = [[0.5] * n_types for _ in range(n_agents)]
    utilities = []
    harmful = []

    for t in range(steps):
        if t == shift_t:
            capabilities = [[rng.random() for _ in range(n_types)] for _ in range(n_agents)]

        info_type = rng.randrange(n_types)
        sender = rng.randrange(n_agents)
        message_quality = 0.8 if rng.random() < 0.8 else 0.25
        budget = 3
        population = [i for i in range(n_agents) if i != sender]

        if mode == "push":
            chosen = sorted(population, key=lambda i: sender_estimate[i][info_type], reverse=True)[:budget]
        elif mode == "pull":
            candidates = [i for i in population if capabilities[i][info_type] >= 0.58]
            rng.shuffle(candidates)
            chosen = candidates[:budget]
            while len(chosen) < budget:
                x = rng.choice(population)
                if x not in chosen:
                    chosen.append(x)
        elif mode == "negotiated":
            shortlist = sorted(population, key=lambda i: sender_estimate[i][info_type], reverse=True)[: budget * 3]
            chosen = [i for _, i in sorted(((capabilities[i][info_type], i) for i in shortlist), reverse=True)[:budget]]
        else:
            chosen = rng.sample(population, budget)

        for receiver in chosen:
            capability = capabilities[receiver][info_type]
            utility = message_quality * capability - (1.0 - message_quality) * (1.0 - capability) * 0.8
            utilities.append(utility)
            harmful.append(utility < 0.0)

            observed = max(0.0, min(1.0, capability + rng.gauss(0.0, 0.12)))
            sender_estimate[receiver][info_type] = 0.9 * sender_estimate[receiver][info_type] + 0.1 * observed

    mid = len(utilities) // 2
    return {
        "seed": seed,
        "mode": mode,
        "pre_utility": statistics.mean(utilities[:mid]),
        "post_utility": statistics.mean(utilities[mid:]),
        "mean_utility": statistics.mean(utilities),
        "harmful_rate": statistics.mean(harmful),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=400)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = [run(seed, mode) for mode in MODES for seed in range(args.seeds)]
    summary = {}
    for mode in MODES:
        sub = [r for r in rows if r["mode"] == mode]
        summary[mode] = {
            "n": len(sub),
            "pre_utility_mean": statistics.mean(r["pre_utility"] for r in sub),
            "post_utility_mean": statistics.mean(r["post_utility"] for r in sub),
            "mean_utility": statistics.mean(r["mean_utility"] for r in sub),
            "harmful_rate": statistics.mean(r["harmful_rate"] for r in sub),
        }

    result = {"schema": "adaptive-evolution.sender-receiver-negotiation.v0.1", "summary": summary}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for mode, stats in summary.items():
            print(mode, stats)


if __name__ == "__main__":
    main()

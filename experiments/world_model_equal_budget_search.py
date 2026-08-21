from __future__ import annotations

import argparse
import json
import math
import random
import statistics


def trial(seed: int, policy: str, steps: int = 120, shift_t: int = 30,
          budget: int = 12) -> dict:
    rng = random.Random(seed)
    pool = [
        {
            "x": min(1.0, max(0.0, rng.gauss(0.25, 0.08))),
            "score": 0.0,
            "n": 0,
            "contra": 0,
        }
        for _ in range(8)
    ]
    births = 0
    first_good = None

    constant_times = set(
        round(shift_t + i * (steps - shift_t - 1) / (budget - 1))
        for i in range(budget)
    )

    for t in range(steps):
        optimum = 0.25 if t < shift_t else 0.75

        for candidate in rng.sample(pool, min(3, len(pool))):
            rare = rng.random() < 0.25
            slope = 2.8 if rare else 1.6
            mu = max(0.0, 1.0 - slope * abs(candidate["x"] - optimum))
            if not rare:
                mu = min(
                    1.0,
                    mu + 0.15 * math.exp(-((candidate["x"] - 0.25) / 0.10) ** 2),
                )
            reward = min(1.0, max(0.0, rng.gauss(mu, 0.06)))
            candidate["n"] += 1
            alpha = 0.25 if candidate["n"] < 8 else 0.12
            candidate["score"] = (
                (1.0 - alpha) * candidate["score"] + alpha * reward
            )
            if rare and reward < 0.25:
                candidate["contra"] += 1
            elif rare and reward > 0.65:
                candidate["contra"] = max(0, candidate["contra"] - 1)

        generate = False
        if t >= shift_t and births < budget:
            if policy == "constant":
                generate = t in constant_times
            elif policy == "triggered":
                best = max(pool, key=lambda item: item["score"])
                generate = best["contra"] >= 2
            elif policy == "hybrid":
                best = max(pool, key=lambda item: item["score"])
                generate = best["contra"] >= 2 or (t - shift_t) % 12 == 0
            else:
                raise ValueError(policy)

        if generate:
            top = sorted(pool, key=lambda item: item["score"], reverse=True)[:3]
            parent = rng.choice(top)
            sigma = (
                0.16
                if policy == "constant"
                else min(0.30, 0.12 + 0.04 * parent["contra"])
            )
            x = min(1.0, max(0.0, rng.gauss(parent["x"], sigma)))
            pool.append({"x": x, "score": 0.0, "n": 0, "contra": 0})
            births += 1
            if policy != "constant":
                parent["contra"] = max(0, parent["contra"] - 1)

        # Budget equalization. Triggered/hybrid policies may not naturally spend
        # their full budget, so remaining births are forced at the final slots.
        remaining_steps = steps - t - 1
        remaining_births = budget - births
        if (
            policy != "constant"
            and remaining_births > 0
            and remaining_steps < remaining_births
        ):
            parent = max(pool, key=lambda item: item["score"])
            x = min(1.0, max(0.0, rng.gauss(parent["x"], 0.18)))
            pool.append({"x": x, "score": 0.0, "n": 0, "contra": 0})
            births += 1

        if (
            t >= shift_t
            and first_good is None
            and any(
                abs(candidate["x"] - optimum) < 0.10
                and candidate["score"] > 0.45
                for candidate in pool
            )
        ):
            first_good = t - shift_t

    best = max(pool, key=lambda item: item["score"])
    horizon = steps - shift_t
    return {
        "first_good": first_good if first_good is not None else horizon,
        "success": first_good is not None,
        "final_best_distance": abs(best["x"] - 0.75),
        "births": births,
        "final_pool": len(pool),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=600)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {
        "schema": "adaptive-evolution.world-model-equal-budget-search.v0.1",
        "seeds": args.seeds,
        "conditions": {},
    }

    for policy in ("constant", "triggered", "hybrid"):
        rows = [trial(seed, policy) for seed in range(args.seeds)]
        result["conditions"][policy] = {
            "first_good_median": statistics.median(r["first_good"] for r in rows),
            "first_good_mean": statistics.mean(r["first_good"] for r in rows),
            "success_rate": statistics.mean(float(r["success"]) for r in rows),
            "final_best_distance_mean": statistics.mean(
                r["final_best_distance"] for r in rows
            ),
            "births_mean": statistics.mean(r["births"] for r in rows),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, stats in result["conditions"].items():
            print(name, stats)


if __name__ == "__main__":
    main()

# Typed Tool Transfer and Transaction Boundary — 2026-08-23

## Question

Does the synthetic architecture survive transfer from abstract actions to structured tool calls with explicit hard constraints, stale metadata, root outages, fallback failures, security-attribute manipulation, and validate/execute races?

This is still a **synthetic proposer + mock tool runtime**, not a live LLM benchmark. The transfer target is the enforcement architecture and failure structure, not natural-language reasoning quality.

## Tool classes

Four explicit tool classes were used:

1. `read(namespace, key)` — read-only;
2. `write(key, delta)` — bounded reversible update;
3. `delete(key)` — irreversible/destructive;
4. `transfer(src, dst, amount)` — bounded resource transfer.

The proposer outputs a structured call plus self-reported utility/confidence/safety. The external hard gate does not trust those self-reports.

## Main typed-tool transfer — 64 paired seeds / scenario

### Clean

| policy | utility | success | leak | runs with violation |
|---|---:|---:|---:|---:|
| actor self-report | 0.9950 | 0.996 | 0 | 0 |
| noisy external | 0.9467 | 0.944 | 0.0003 | 0.094 |
| typed degraded | 0.9961 | 1.000 | 0 | 0 |

The hard layer does not require a clean-task utility sacrifice in this scenario.

### Manipulation

| policy | utility | leak | runs with violation |
|---|---:|---:|---:|
| actor self-report | 0.7413 | 0.1388 | 1.000 |
| noisy external | 0.8216 | 0.0104 | 0.984 |
| typed degraded | **0.9078** | **0** | **0** |

Typed degraded minus actor self-report utility:

`+0.16655 [0.16041, 0.17269]`

Leak difference:

`-0.13876 [-0.14370, -0.13382]`

### Drift / stale metadata

| policy | utility | leak | runs with violation |
|---|---:|---:|---:|
| actor self-report | 0.4783 | 0.2780 | 1.000 |
| noisy external | 0.6844 | 0.0229 | 1.000 |
| typed stale-continue | 0.5340 | 0.2333 | 1.000 |
| typed current/versioned | **0.8140** | **0** | **0** |

A typed gate that continues to use correctly signed but stale policy metadata is still unsafe. Type checking does not solve freshness.

### Root outage

| policy | utility | leak | false block | mode occupancy |
|---|---:|---:|---:|---:|
| typed stale-continue | 0.5464 | 0.2272 | 0 | stale |
| typed fail-closed | 0.7690 | 0 | 0.045 | fail-closed 0.167 |
| typed coarse degraded | **0.8077** | **0** | **0.017** | degraded 0.167 |

Coarse degraded minus fail-closed utility:

`+0.03870 [0.03676, 0.04063]`

False-block difference:

`-0.02717 [-0.02963, -0.02471]`

### Combined manipulation + drift + root outage + fallback common-mode

| policy | utility | success | leak | runs with violation |
|---|---:|---:|---:|---:|
| actor self-report | 0.3388 | 0.640 | 0.3548 | 1.000 |
| noisy external | 0.6132 | 0.609 | 0.0288 | 1.000 |
| typed stale-continue | 0.4963 | 0.746 | 0.2178 | 1.000 |
| typed fail-closed | 0.7025 | 0.844 | 0 | 0 |
| typed degraded | **0.7349** | **0.911** | **0** | **0** |

Typed degraded minus fail-closed utility:

`+0.03235 [0.03069, 0.03401]`

## Tool-class breakdown — independent 64-seed combined run

Leak rates by original requested tool:

| policy | read | write | delete | transfer |
|---|---:|---:|---:|---:|
| actor self-report | 0.2510 | 0.3513 | 0.5417 | 0.2848 |
| noisy external | 0.0220 | 0.0301 | 0.0430 | 0.0236 |
| typed stale-continue | 0 | 0.2325 | 0.4493 | 0.1864 |
| typed degraded | **0** | **0** | **0** | **0** |

The result is not driven by only one tool class. Staleness is especially destructive for write/delete/transfer, while immutable read namespace constraints remain enforceable even under stale policy metadata.

## Authority binding: typed schema is not enough

A flaw was then intentionally introduced: the actor could supply a security-relevant field such as `protected=false`.

The correct comparison is therefore not “typed vs untyped” but:

- actor-supplied security metadata;
- external authoritative registry;
- stale external registry;
- versioned registry with fail-closed/degraded behavior.

64-seed manipulation + drift + root-outage result:

| policy | utility | leak | runs with violation | false block |
|---|---:|---:|---:|---:|
| actor-field gate | 0.5036 | 0.2486 | 1.000 | 0 |
| stale registry | 0.7952 | 0.0603 | 1.000 | 0 |
| versioned fail-closed registry | 0.8326 | 0 | 0 | 0.1238 |
| versioned coarse-degraded registry | **0.8819** | **0** | **0** | **0.0147** |

Coarse-degraded registry minus actor-field gate leak:

`-0.24857 [-0.25343, -0.24370]`

Coarse-degraded registry minus fail-closed utility:

`+0.04926 [0.04812, 0.05040]`

Clean 64-seed control (`manip_p=0`):

- actor-field gate utility: 1.0005, leak 0;
- registry degraded utility: 0.9915, leak 0, false block 0.0197;
- registry fail-closed utility: 0.9251, false block 0.1667.

**Decision:** security-relevant attributes must be resolved from an external authority/registry. They must not be accepted as actor-owned tool arguments merely because the call is schema-valid.

## Terminal enforcement faults in typed-tool runtime

The main typed architecture initially assumed local hold/suspension always worked. That assumption was then removed.

Combined scenario, 64 paired seeds:

| terminal mechanism | utility | leak | runs with violation |
|---|---:|---:|---:|
| single hold | 0.7209 | 0.01315 | 1.000 |
| dual hold | 0.7290 | 0.00399 | 0.703 |
| independent capability cut | **0.7327** | **0** | **0** |
| delayed capability cut | 0.7265 | 0.00399 | 0.703 |
| capability cut with 10% failure | 0.7324 | 0.00035 | 0.109 |

Independent cut minus delayed cut leak:

`-0.003993 [-0.004931, -0.003055]`

Independent cut minus dual hold run-level violation:

`-0.7031 [-0.8159, -0.5903]`

**Decision:** an emergency stop command is not a hard boundary unless it takes effect before unsafe dispatch. Redundant holds reduce failure probability but do not replace an independent terminal capability cut.

## TOCTOU: validation is not enough without commit atomicity

Structured certification was initially atomic with execution. Real tools need not satisfy that assumption, so a concurrent resource-race benchmark was added.

Policies:

1. `check_then_use` — validate, allow state change, execute without recheck;
2. `recheck_before_commit` — recertify immediately before commit;
3. `reservation_token` — atomically reserve the bounded resource at validation, then commit the reserved capability.

Reservation overhead was set to `0.002 utility / call` so reservation is not artificially free.

### Race probability 5%, 64 seeds

| policy | utility | leak | runs with violation | abort |
|---|---:|---:|---:|---:|
| check-then-use | 0.99977 | 0.00013 | 0.078 | 0 |
| recheck | **0.99989** | 0 | 0 | 0.00013 |
| reservation | 0.99800 | 0 | 0 | 0 |

Reservation minus recheck utility:

`-0.001893 [-0.001984, -0.001803]`

### Race probability 18%

| policy | utility | leak | runs with violation | abort |
|---|---:|---:|---:|---:|
| check-then-use | 0.99644 | 0.00198 | 0.688 | 0 |
| recheck | **0.99838** | 0 | 0 | 0.00198 |
| reservation | 0.99800 | 0 | 0 | 0 |

Reservation is slightly worse than recheck at this cost:

`-0.000377 [-0.000744, -0.000010]`

### Race probability 35%

| policy | utility | leak | runs with violation | abort |
|---|---:|---:|---:|---:|
| check-then-use | 0.97713 | 0.01271 | 1.000 | 0 |
| recheck | 0.99007 | 0 | 0 | 0.01211 |
| reservation | **0.99800** | **0** | **0** | **0** |

Reservation minus recheck utility:

`+0.007930 [0.006804, 0.009056]`

**Decision:** type validation must be bound to the eventual execution state. Rechecking is efficient at low contention; atomic reservation/capability tokens become preferable when contention/race probability is high enough. The transaction boundary is therefore part of the safety architecture.

## H / T / D / C / U

### H

A structured external capability architecture can prevent uncertified tool-call leakage under ordinary proposer manipulation, stale actor beliefs, verifier/root outages, and fallback faults, provided that security attributes and commit state are outside actor control and the declared TCB remains correct.

### T

- 64 paired seeds per main scenario;
- 64 paired seeds for authority binding;
- 64 paired seeds for terminal interlock faults;
- 64 paired seeds per TOCTOU contention level;
- same generated task/noise trajectory within each paired comparison.

### D

PASS at this synthetic interface layer:

- ordinary faults outside the declared TCB do not force an uncertified call through `typed_degraded`;
- stale metadata and actor-owned security metadata are explicitly shown to violate the guarantee;
- hard guarantee remains conditional on immediate terminal enforcement;
- clean-task utility remains materially above unconditional fail-closed;
- safe degraded operation outperforms unconditional fail-closed during root outage.

### C — failure modes / alternative hypotheses

The transfer is not complete because:

1. proposals are generated by a synthetic policy, not a live LLM;
2. Python `Call` objects bypass JSON/wire-format parsing;
3. parser coercion, unknown fields, NaN/overflow, unit ambiguity and schema-version confusion are not yet tested;
4. transaction reservation is an idealized primitive;
5. tool-side implementation bugs and remote-service semantics are not modeled;
6. no cryptographic implementation is actually exercised.

### U

The reported zero-leak results are conditional on the simulated registry/version bulletin/coarse cap/capability cut being correct. They are not unconditional real-world safety guarantees.

## Architectural update

```text
LLM / proposer
   |
   | structured proposal + self-reported utility/confidence
   v
STRICT DECODER (next gate)
   |
   v
AUTHORITATIVE resource/capability binding
   |
   v
version / freshness state
   |
   +--> current: exact typed gate
   +--> root unavailable: immutable coarse degraded gate
   +--> uncertifiable: fail closed
   |
   v
commit binding
   +--> low contention: commit-time recheck
   +--> high contention: reservation/capability token
   |
   v
cross-domain fallback
   v
local hold
   v
independent capability cut
   v
tool runtime
```

## Decision

The typed-tool transfer gate is **conditionally passed** at the mock-runtime layer.

The next gate should not tune these thresholds. It should attack the wire-format and parser boundary, then introduce a live/frozen LLM proposer while keeping the enforcement code external to the model.

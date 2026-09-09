# Organizational memory: delay reduction vs common-cause failure

## Scope

Synthetic mechanism follow-up. Four agents, 20 task types, 400 training steps and 600 evaluation steps. Acquisition lookup cost is 0.05 normalized utility; fallback lookup cost is 0.20. A one-source corruption occurs with the stated episode probability. No live Hermes or provider call is involved.

## Single shared memory reduces acquisition delay but amplifies poison

A preliminary 5,000-replication experiment found:

- private per-agent memory: ~79.86 acquisition queries; ~12.50 poisoned evaluation errors;
- one authoritative shared entry: 20 acquisition queries; ~50.04 poisoned evaluation errors;
- provenance-separated 3-source memory: ~60 acquisition queries; 0 poisoned errors, but ~37.58 unresolved/fallback evaluation rows under the fixed training budget.

This directly expresses the organization's delay/risk tradeoff: sharing knowledge removes repeated acquisition, but one shared authoritative entry becomes a common-cause failure surface.

## Quorum FCV follow-up

A 1,000-replication follow-up evaluates source quorums 1/2/3/4 with acquisition, poison-error, and fallback costs on the same utility scale.

| Probability of one-source poison | Best quorum | q=1 net loss | q=2 | q=3 | q=4 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 1 | 1.000 | 2.000 | 3.036 | 6.962 |
| 0.01 | 1 | 1.316 | 2.063 | 3.029 | 7.170 |
| 0.05 | 2 | 2.600 | 2.320 | 3.054 | 7.195 |
| 0.10 | 2 | 4.268 | 2.654 | 3.033 | 6.921 |
| 0.25 | 3 | 8.851 | 3.570 | 3.010 | 7.155 |
| 0.50 | 3 | 15.695 | 4.939 | 3.043 | 7.144 |
| 1.00 | 3 | 30.885 | 7.977 | 3.034 | 7.098 |

The numerical switching points are benchmark-specific, but the qualitative result is stable in this construction:

> `Memory replication / authority quorum is an FCV coordinate.`

and:

> `Knowledge-sharing latency != evidence independence.`

A low quorum is efficient in clean environments; higher provenance-separated support becomes worth paying for when common-cause corruption risk grows.

## Limitations

The source-agent observations are synthetic and correctly labeled before corruption. The fallback oracle is assumed correct. A single-source corruption model is not an estimate of real-world memory poisoning frequency. Quorum counts do not by themselves prove independent provenance; real implementations need dependency-group accounting from the broader research program.

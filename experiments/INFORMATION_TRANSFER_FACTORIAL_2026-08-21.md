# Information transfer factorial pilot — 2026-08-21

Purpose: avoid the invalid generalization that "faster propagation is always better" or that sender/receiver/target can be collapsed into one variable.

## Design

Toy system with three receiver roles: executor, verifier, archive.

Factors:
- speed: fast / slow;
- routing: broadcast / role-targeted / mixed;
- representation: raw / compressed / abstract;
- receiver: local-only / context-aware.

All routing policies use the same message budget (3 recipients per event). Environment changes halfway through the run. 80 seeds per factorial cell, 36 cells total.

A separate channel experiment isolates information type and gives the slow channel an explicit semantic correction benefit for verification/pattern/abstract information, while action/warning information remains strongly time-sensitive. 100 seeds per type/speed.

## Equal-budget marginal results

| Factor | Level | Action accuracy | Useful delivery rate | Harmful delivery rate |
|---|---|---:|---:|---:|
| speed | fast | 0.8901 | 0.4369 | 0.1769 |
| speed | slow | 0.8719 | 0.3395 | 0.1641 |
| routing | broadcast | 0.8751 | 0.2724 | 0.2590 |
| routing | targeted | **0.8849** | **0.4703** | **0.1071** |
| routing | mixed | 0.8830 | 0.4220 | 0.1455 |
| receiver | local-only | 0.8615 | 0.3798 | 0.1842 |
| receiver | context-aware | **0.9006** | **0.3967** | **0.1568** |

Interpretation: once bandwidth is equalized, role-targeted routing beats broadcast on action accuracy and strongly improves useful/harmful delivery ratio. This reverses an earlier unequal-budget pilot in which broadcast looked best simply because it sent more copies.

Representation effects were small in the aggregate because information types were mixed; therefore no universal raw/compressed/abstract ordering is claimed.

## Information-type × speed crossover

Mean channel value under matched targets and context-aware receivers:

| Information type | Fast | Slow |
|---|---:|---:|
| action | **0.533** | 0.176 |
| warning | **0.560** | 0.185 |
| verification | **0.551** | 0.441 |
| pattern | **0.485** | 0.463 |
| abstract | 0.365 | **0.438** |

This toy model exhibits a real crossover: fast transfer dominates for action/warning; slower deliberative transfer can dominate for abstract information when delay buys semantic correction and the receiver can tolerate latency.

## Current inference

Do not optimize one global propagation speed. The next architecture should treat transfer policy as conditional on at least:

`information type × sender state × receiver role/state × target set × representation × deadline × verification state`.

"Useful information" should be scored by downstream receiver-state/outcome change, not by transmission count or sender confidence.

## Important negative result

An earlier pilot used 8 recipients for broadcast and 3 for targeted routing. Broadcast then had higher aggregate action accuracy. Equalizing the message budget reversed that result. Therefore bandwidth is a confounder and must remain controlled in future routing experiments.

## Next experiment

Move from hand-coded receiver roles to latent receiver capabilities. Test whether a learned/estimated routing rule can choose recipient, representation and latency class from local observable state without being given the labels executor/verifier/archive.

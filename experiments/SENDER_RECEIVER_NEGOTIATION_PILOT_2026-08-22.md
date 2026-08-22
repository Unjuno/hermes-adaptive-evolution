# Sender / Receiver Negotiation Pilot — 2026-08-22

Toy simulation, 400 seeds per routing mode, 36 agents, 3 information types, 220 steps. Receiver capabilities are redrawn at step 110. All modes use the same bandwidth budget: 3 recipients per message.

## Results

| mode | pre utility | post utility | mean utility | harmful rate |
|---|---:|---:|---:|---:|
| random | 0.2203 | 0.2219 | 0.2211 | 0.2749 |
| push | 0.4685 | 0.4037 | 0.4361 | 0.0967 |
| pull | 0.4915 | 0.4934 | 0.4925 | 0.0598 |
| negotiated | **0.5312** | **0.5216** | **0.5264** | **0.0341** |

## Interpretation

- Sender-only push routing performs well before the capability shift but degrades after the receiver population changes because sender-side estimates become stale.
- Receiver-side pull remains stable across the shift because receivers use current local capability, but it relies on self-selection and does not exploit sender-side targeting as effectively.
- Negotiated routing, where the sender supplies a shortlist and receivers contribute current local capability, performs best under this toy model and produces the lowest harmful-transfer rate.
- This does **not** prove negotiation is universally optimal. The simulation gives receivers unusually accurate self-knowledge and coordination inside the shortlist is idealized.

## Decision

Promote a new hypothesis: routing should be decomposed into at least two decisions rather than assigned entirely to sender or receiver:

1. sender-side relevance / candidate-recipient filtering;
2. receiver-side acceptance / current-state compatibility.

Next control: introduce noisy or strategically biased receiver self-estimates and explicit negotiation latency/cost. If negotiated routing loses its advantage under modest self-knowledge error or cost, retain push/pull hybrids instead of a negotiation primitive.

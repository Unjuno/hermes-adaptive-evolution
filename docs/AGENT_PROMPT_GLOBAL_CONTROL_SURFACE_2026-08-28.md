# Agent Prompt as a Global Control Surface — 2026-08-28

The Agent Prompt and the stochastic organizational transition model are distinct control variables.

- `theta_prompt` changes the action/proposal distribution produced **inside** a workflow state.
- `phi_org` changes which workflow/agent state is visited next.

Because one Agent Prompt version is reused across many downstream actions, a fixed-cost prompt improvement can have horizon-wide leverage. This does not imply that Prompt should be optimized forever: once its marginal downstream gain/cost falls below another control surface, resource allocation should move.

## AP-1 — Fixed-cost Agent Prompt leverage

Synthetic profiles: 60,000.

Mean proposal correctness:
- base Agent Prompt: 68.64%
- optimized Agent Prompt: 82.76%

A Prompt optimization costs `4.0` normalized units once per version. Verification costs `0.075` per action.

| Reuse horizon | Prompt gain/cost | Verification gain/cost | Prompt / verifier ROI |
|---:|---:|---:|---:|
| 1 | 0.0177 | 0.2145 | 0.08x |
| 5 | 0.0883 | 0.2145 | 0.41x |
| 20 | 0.3534 | 0.2145 | 1.65x |
| 100 | 1.7669 | 0.2145 | 8.24x |
| 500 | 8.8344 | 0.2145 | 41.19x |
| 2,000 | 35.3376 | 0.2145 | 164.77x |

Model-specific ROI break-even: **13 actions**.

Decision: positive mechanism evidence that a reused Agent Prompt can become a high-leverage bottleneck. The numerical break-even is not a real Humies estimate.

## AP-2 — Prompt optimization vs stochastic organization

2x2 factorial ablation over 18,000 paired episodes x 300 steps.

| Prompt | Organization | Mean welfare | Prompt-failure action rate |
|---|---|---:|---:|
| base | context-blind | 0.589825 | 27.83% |
| optimized | context-blind | 0.661994 | 10.71% |
| base | context-aware | 0.676248 | 27.84% |
| optimized | context-aware | **0.758542** | 10.70% |

Gains over baseline:
- Prompt only: +0.072169
- Organization only: +0.086423
- Joint: +0.168717
- interaction beyond additive gains: +0.010125

Decision: Prompt and organizational-transition optimization are not substitutes. They control different failure surfaces and jointly perform best in this synthetic mechanism.

## AP-3 — Causal bottleneck allocation

Initial qualities: Prompt 0.61, Organization 0.74, Execution 0.88. Episode horizon: 200; normalized optimization budget: 28.

| Strategy | Total utility gain |
|---|---:|
| Prompt only | 23.4382 |
| Round robin | 21.5941 |
| **Causal marginal gain/cost** | **30.1694** |

Causal allocation path:

`prompt -> prompt -> organization -> prompt -> organization -> prompt -> organization`

Decision: the Agent Prompt is initially the dominant bottleneck, but it does not remain the bottleneck after improvement. The allocator moves between Prompt and Organization.

## AP-4 — Long-horizon Agent Prompt self-edit

Benign self-edit regime, 16,000 episodes x 700 steps.

Under benign candidate edits, auditing every edit did not materially beat immutable/versioned overlays. Always-audit is therefore not justified by prompt importance alone.

## AP-4b — Prompt self-edit reward hacking

After step 300, 18% of candidate edits were allowed to improve proxy/domain dimensions while degrading `constraints` and `tool_semantics`.

| Policy | True action utility | Accepted malicious edits | Protected quality mean | Protected quality p05 |
|---|---:|---:|---:|---:|
| in-place rewrite | 0.939599 | 9.03 | 0.843 | 0.590 |
| immutable overlay | 0.957444 | 7.41 | 0.906 | 0.673 |
| **audited overlay** | **0.973782** | **1.81** | **0.992** | **0.976** |

Decision: under self-edit reward hacking, the Prompt Supply Chain becomes a security-relevant adaptive-control boundary. Immutable provenance and protected-dimension audit materially help, while the downstream hard runtime remains independent.

## Unified architecture

```text
belief/context -> stochastic workflow kernel P_phi -> agent placement

immutable base Agent Prompt theta_0
  + versioned/approved overlays
  -> agent action distribution pi_theta

prompt supply chain:
  impact locator -> candidate edit -> protected-dimension audit when triggered
  -> version/provenance binding -> active Agent Prompt

hard runtime:
  proposal -> semantic invariant -> authoritative commit -> effect
```

Prompt optimization and transition-kernel optimization should be separate modules coordinated by the same marginal downstream gain/cost allocator.

## Decision summary

- Agent Prompt long-horizon leverage: positive evidence.
- Prompt-only forever: rejected as an allocation rule.
- Prompt + stochastic organization: positive joint result.
- always-audit benign prompt edits: not supported.
- audited immutable overlay under reward-hacked self-edit: strong positive mechanism evidence.

All results here are synthetic mechanism evidence, not real-LLM production estimates. The next empirical gap is a controlled frozen/live LLM Agent Prompt benchmark when an independent sampling runner is available.
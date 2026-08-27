# Agent Prompt / Probabilistic Organization Progress — 2026-08-28

New retained findings:

- Agent Prompt is modeled as a global action-policy control surface, distinct from the stochastic organization transition kernel.
- AP-1: fixed-cost prompt improvement becomes increasingly favorable as one prompt version is reused across a longer autonomous trajectory; model-specific ROI break-even was 13 actions.
- AP-2: prompt optimization and context-aware organizational routing both improve welfare and jointly perform best.
- AP-3: causal bottleneck allocation starts with Prompt but moves to Organization after Prompt improves; prompt-only optimization is not the best allocation rule.
- AP-4: under benign prompt self-editing, always-on edit auditing adds little over immutable/versioned overlays.
- AP-4b: under reward-hacked self-edits that improve proxy dimensions while degrading protected semantics, audited immutable overlays materially preserve protected prompt quality.
- Hard runtime authority remains external to Agent Prompt quality and Prompt Supply Chain decisions.

Next:

1. real/frozen LLM Agent Prompt ablation when an independent model runner is available;
2. PSM-8 combined semantic sleeper attack with mutating action surface + prompt-edit surface;
3. risk-triggered Prompt audit rather than always-on audit;
4. joint bottleneck allocator over Prompt, stochastic organization, telemetry verification, and execution.
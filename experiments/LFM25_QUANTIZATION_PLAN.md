# LFM2.5-2.6B Quantization / QLoRA Experiment Plan

This track tests whether LFM2.5-2.6B is a better local adaptive-agent substrate than the current Qwen3 4B fixture. It deliberately separates **inference quantization** from **training quantization**.

## Model targets

- Native/post-trained: `LiquidAI/LFM2.5-2.6B`
- Base checkpoint for heavier specialization: `LiquidAI/LFM2.5-2.6B-Base`
- Local inference artifact: `LiquidAI/LFM2.5-2.6B-GGUF:Q4_K_M`
- Training path: Unsloth/PEFT 4-bit load + LoRA (QLoRA), not direct GGUF weight updates

The official model has 2.69B parameters, 30 blocks (22 convolution + 8 GQA attention), 128K context, and agentic post-training. The official GGUF Q4_K_M artifact is ~1.67 GB. Liquid AI also documents LoRA SFT/DPO/GRPO and 4-bit loading through Unsloth.

## Hypotheses

### LFM-H1 — local Hermes viability

At an equal or smaller memory footprint than the current Qwen3 4B local fixture, LFM2.5-Q4 can complete the provider-backed E1 path:

`root -> delegate_task -> child -> deterministic tool failure -> repair -> tool success -> completion`

This is an observability/runtime hypothesis, not a general coding-quality claim.

### LFM-H2 — iteration-density advantage

For a fixed local GPU-hour budget, 4-bit QLoRA permits more adapter candidates / hyperparameter trials than BF16 or larger local models, increasing the chance of finding a better validated Pareto candidate.

Primary outcome is **best held-out decision utility per GPU-hour**, not training loss.

### LFM-H3 — fine-tuning sensitivity

Small amounts of verified trajectory data may produce larger behavioral changes in this compact model. This is an empirical hypothesis, not a universal consequence of quantization or parameter count.

Measure both useful gain and regression sensitivity.

## Phase A — inference / Hermes E1

Compare on the exact same deterministic E1 fixture:

1. Qwen3 4B Q4 baseline
2. LFM2.5-2.6B Q4_K_M

Record:

- model artifact size;
- configured/runtime context;
- model preload wall time;
- Hermes wall time;
- E1 pass/fail;
- valid delegation start/stop;
- tool-call parse validity;
- failure -> recovery observation;
- repair verification;
- normalized event count;
- hook field coverage;
- identity uncertainty;
- corruption/replay robustness.

A model failure is only attributed to model behavior after runtime/context/provider failures are excluded.

## Phase B — quantization quality ladder

On a fixed held-out agent task set, compare:

- native BF16 inference (reference where hardware permits);
- Q8_0;
- Q6_K;
- Q5_K_M;
- Q4_K_M.

Use paired tasks and deterministic external fixtures where possible.

Metrics:

- task success;
- tool-call syntax success;
- recovery rate;
- teacher escalation rate;
- latency / tokens per second;
- peak RAM/VRAM;
- rare catastrophic failure rate.

Do not select a quant solely on average benchmark score.

## Phase C — QLoRA sample-complexity experiment

Train from the native model with 4-bit loading and LoRA adapters. Initial controlled grid:

- verified trajectories: 32 / 64 / 128 / 256;
- sequence length: 1024 / 2048 / 4096 as memory permits;
- LoRA rank: 8 / 16 / 32;
- alpha: 16 / 32 / 64;
- seeds: >= 3 for any promotion decision;
- data views kept separate: clean success / recovered success / teacher correction / failure or preference evidence.

Start with attention + MLP target modules following the supported Liquid/Unsloth path. Add convolution-specific targets only after parameter-name inspection and an explicit ablation.

Measure:

- wall time;
- peak VRAM;
- examples/tokens per second;
- held-out task success;
- recovery rate;
- tool-call validity;
- golden-regression failure rate;
- teacher-call reduction;
- behavior distance from base;
- seed variance.

The key curve is:

`validated behavioral gain / GPU-hour`

not `training loss / step`.

## Phase D — candidate-factory test

Fix one total compute budget and compare strategies:

- one larger/longer LoRA run;
- many short candidate LoRAs + benchmark + Pareto selection;
- adaptive racing that stops weak candidates early.

Track how many independent candidates reach final validation per GPU-hour and whether increased candidate count actually improves the held-out Pareto frontier.

## Safety / promotion rule

No adapter is promoted directly from training metrics.

`candidate -> independent benchmark -> golden regression -> rare-event suite -> canary -> promote/reject/rollback`

GGUF Q4 inference artifacts and QLoRA training state are separate artifacts with separate provenance.

## Falsification conditions

Downgrade the LFM2.5 track if any of these persist after runtime issues are removed:

- unreliable function/tool-call syntax;
- provider-backed E1 cannot delegate or recover;
- Q4 causes meaningful rare-event regressions relative to Q5/Q6;
- QLoRA candidate throughput improves but validated utility per GPU-hour does not;
- fine-tuning sensitivity is mostly catastrophic forgetting rather than useful specialization.

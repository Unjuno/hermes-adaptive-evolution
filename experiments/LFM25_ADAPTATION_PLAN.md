# LFM2.5-2.6B Adaptation Experiment Plan

This plan tests whether LFM2.5-2.6B's small footprint improves the **rate of validated adaptation**, not merely inference memory use.

## Model artifacts are not interchangeable

- `LiquidAI/LFM2.5-2.6B` (native BF16/safetensors): reference checkpoint for training and inference.
- 8-bit / 4-bit *training load*: quantized base weights used while learning LoRA adapters (QLoRA-style). This is a training configuration.
- `LiquidAI/LFM2.5-2.6B-GGUF:Q4_K_M`: deployment/inference artifact for llama.cpp/Ollama. Do **not** treat GGUF Q4 as the training checkpoint.
- Deployment comparison should quantize the merged/base+adapter result separately after training when needed.

## Hypotheses

### H-LFM-1 — E1 viability

The official Q4_K_M deployment artifact can execute Hermes tool/delegation/failure-recovery paths without external API credentials.

Status: **supported by the first provider-backed E1 run**; repeatability is still unmeasured.

### H-LFM-2 — adaptation throughput

At fixed wall-clock and hardware budget, low-bit training load permits more LoRA candidates to be trained and evaluated than BF16 while retaining enough quality to improve the Pareto frontier.

### H-LFM-3 — quantization sensitivity

Lower-bit loading may change adaptation sensitivity. This is an empirical question; do not assume that smaller quantization universally improves fine-tuning.

### H-LFM-4 — specialization complementarity

Multiple narrow LoRAs may outperform one globally tuned adapter when measured by conditional success and complementarity, especially `P(B succeeds | A fails)`.

## Phase A — inference contract

Use the deterministic E1 repair fixture with the same pinned Hermes revision.

Compare at minimum:

1. LFM2.5-2.6B Q4_K_M local inference;
2. a same-class small local baseline (currently Qwen3 4B Q4 history exists, but its first E1 was confounded by context failure);
3. optionally LFM2.5 Q5/Q8 only if Q4 failure suggests a quantization-quality issue.

Measure:

- tool-call probe pass/fail;
- `delegate_task` start/stop;
- deterministic failure -> recovery;
- final fixture correctness;
- wall time;
- peak memory when measurable;
- normalized event count;
- identity uncertainty;
- corruption/replay robustness.

Do not interpret this as a general coding benchmark.

## Phase B — training-load comparison

Use identical verified training examples, seeds, LoRA target modules, rank, alpha, optimizer and token budget unless the factor under test requires otherwise.

Arms:

1. native/BF16 base + LoRA;
2. 8-bit base load + LoRA;
3. 4-bit base load + LoRA (QLoRA-style).

The GGUF Q4 inference file is **not** an arm in this training experiment.

Record:

- GPU peak allocated/reserved memory;
- examples/s and tokens/s;
- wall time to candidate;
- optimizer steps;
- train/validation loss;
- held-out task success;
- recovery success;
- terminal failure rate;
- rare regression count;
- inference latency after deployment quantization;
- adapter size.

Primary comparison is **validated improvement per unit wall-clock / VRAM budget**, not minimum training loss.

## Phase C — candidate factory

Within the best feasible training-load configuration, vary:

- LoRA rank;
- alpha;
- target modules;
- learning rate;
- steps;
- data mixture;
- seed.

Keep candidates immutable. Evaluate with paired task seeds and a golden regression set.

Promotion is Pareto-based across:

- quality/success;
- recovery;
- failure/unsafe regression;
- latency;
- training cost;
- inference memory;
- complementarity with already promoted adapters.

## Phase D — trajectory-derived data

Training data must come from verified behavior, not directly from Skill text.

Keep separate views:

- clean-success SFT;
- recovered-success SFT (only good/recovery portions are positive);
- Teacher-corrected data;
- preference pairs;
- terminal/unsafe failure negatives.

Every example must preserve provenance: task, Skill name/version, model, adapter, Teacher involvement, verification result and trajectory IDs.

## Phase E — internalization test

After training an adapter from Skill-guided trajectories, hide/disable that Skill at evaluation time.

If performance collapses, the adapter did not internalize the behavior; it only co-adapted to the Skill being present.

## Required controls

- same task distribution across training arms;
- independent final-test block;
- paired seeds where practical;
- no production threshold copied from synthetic experiments;
- no adapter promotion from training loss alone;
- rollback artifact for every promoted adapter.

## Hardware gate

The full training experiment starts only when the runtime exposes a usable CUDA GPU. If no GPU is visible, prepare datasets/configs/evaluation only; do not substitute CPU timings as evidence for RTX-class training throughput.

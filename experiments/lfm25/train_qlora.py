from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import Any


DEFAULT_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def load_verified_messages(path: Path, limit: int | None, seed: int) -> list[dict[str, Any]]:
    """Load only explicitly verified positive SFT views.

    The dataset contract intentionally rejects raw trajectories as direct SFT
    examples. A row must already contain a selected positive message view and
    provenance. Failure / ineffective-retry evidence belongs in separate
    preference or correction datasets.
    """
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number}: row is not an object")
        if row.get("verified") is not True:
            continue
        trajectory_class = str(row.get("trajectory_class") or "")
        if trajectory_class in {"terminal_failure", "unsafe_failure", "failure"}:
            continue
        messages = row.get("sft_positive_messages")
        if not isinstance(messages, list) or not messages:
            continue
        if not all(isinstance(m, dict) and m.get("role") and "content" in m for m in messages):
            raise ValueError(f"line {line_number}: invalid sft_positive_messages")
        rows.append({
            "messages": messages,
            "provenance": row.get("provenance") or {},
            "trajectory_class": trajectory_class,
        })
    rng = random.Random(seed)
    rng.shuffle(rows)
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        raise ValueError("no verified positive SFT examples remain after filtering")
    return rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LFM2.5-2.6B 4-bit QLoRA SFT harness")
    p.add_argument("--dataset", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--model", default="LiquidAI/LFM2.5-2.6B")
    p.add_argument("--max-seq-length", type=int, default=2048)
    p.add_argument("--data-limit", type=int)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--dropout", type=float, default=0.0)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--epochs", type=float, default=1.0)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--target-modules", nargs="+", default=DEFAULT_TARGET_MODULES)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_verified_messages(dataset_path, args.data_limit, args.seed)

    config = {
        "schema": "adaptive-evolution.lfm25-qlora-run.v0.1",
        "model": args.model,
        "load_in_4bit": True,
        "max_seq_length": args.max_seq_length,
        "data_examples": len(rows),
        "rank": args.rank,
        "alpha": args.alpha,
        "dropout": args.dropout,
        "learning_rate": args.learning_rate,
        "epochs": args.epochs,
        "max_steps": args.max_steps,
        "batch_size": args.batch_size,
        "grad_accum": args.grad_accum,
        "seed": args.seed,
        "target_modules": list(args.target_modules),
        "dataset": str(dataset_path),
        "output_dir": str(output_dir),
        "training_artifact_type": "qlora_adapter",
        "inference_gguf_is_not_training_checkpoint": True,
    }
    (output_dir / "run-config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.dry_run:
        print(json.dumps(config, indent=2, sort_keys=True))
        return 0

    # Heavy dependencies are imported only for an actual GPU training run so
    # normal CI can validate the data/config contract without CUDA/Unsloth.
    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this QLoRA benchmark; use --dry-run in CPU CI")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.rank,
        target_modules=list(args.target_modules),
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    def render(example: dict[str, Any]) -> dict[str, str]:
        return {
            "text": tokenizer.apply_chat_template(
                example["messages"],
                tokenize=False,
                add_generation_prompt=False,
            )
        }

    dataset = Dataset.from_list(rows).map(render, remove_columns=["messages", "provenance", "trajectory_class"])
    bf16 = bool(torch.cuda.is_bf16_supported())
    train_args = SFTConfig(
        output_dir=str(output_dir / "trainer"),
        dataset_text_field="text",
        max_length=args.max_seq_length,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        logging_steps=1,
        save_strategy="no",
        seed=args.seed,
        bf16=bf16,
        fp16=not bf16,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=model,
        args=train_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    start = time.perf_counter()
    result = trainer.train()
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    peak = int(torch.cuda.max_memory_allocated())
    adapter_dir = output_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    metrics = {
        **config,
        "wall_seconds": elapsed,
        "peak_cuda_bytes": peak,
        "peak_cuda_gib": peak / (1024 ** 3),
        "train_runtime_reported": result.metrics.get("train_runtime"),
        "train_samples_per_second": result.metrics.get("train_samples_per_second"),
        "train_steps_per_second": result.metrics.get("train_steps_per_second"),
        "train_loss": result.metrics.get("train_loss"),
        "cuda_device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "authority": "training_measurement_only",
        "note": "Promotion requires independent behavioral benchmark, regression, rare-event suite, and canary.",
    }
    (output_dir / "run-metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

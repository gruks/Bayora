#!/usr/bin/env python3
"""Train a DistilBERT classifier on the HH-RLHF harmless-base dataset.

Usage:
    python train_hh_rlhf.py --output-dir ./models/hh-rlhf-classifier

This script fine-tunes distilbert-base-uncased on the Anthropic HH-RLHF
harmless-base preference pairs, converting (chosen, rejected) pairs into
binary classification labels (chosen=safe, rejected=harm).

Note: Requires GPU for reasonable training times. Use Google Colab if
local GPU unavailable.
"""

import argparse

from datasets import concatenate_datasets, load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


def main() -> None:
    """Train the HH-RLHF classifier."""
    parser = argparse.ArgumentParser(
        description="Train a DistilBERT classifier on HH-RLHF harmless-base dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/hh-rlhf-classifier",
        help="Directory to save the fine-tuned model (default: ./models/hh-rlhf-classifier)",
    )
    args = parser.parse_args()

    print("Loading HH-RLHF harmless-base dataset...")
    dataset = load_dataset("Anthropic/hh-rlhf", data_dir="harmless-base")
    train_ds = dataset["train"]

    print("Converting preference pairs to binary labels...")

    def to_safe(example: dict) -> dict:
        return {"text": example["chosen"], "label": 1}

    def to_harm(example: dict) -> dict:
        return {"text": example["rejected"], "label": 0}

    safe_ds = train_ds.map(to_safe, remove_columns=train_ds.column_names)
    harm_ds = train_ds.map(to_harm, remove_columns=train_ds.column_names)
    combined = concatenate_datasets([safe_ds, harm_ds])
    split = combined.train_test_split(test_size=0.1, seed=42)

    print("Tokenizing...")
    model_name = "distilbert/distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(examples: dict) -> dict:
        return tokenizer(examples["text"], truncation=True, max_length=512)

    tokenized = split.map(tokenize, batched=True)

    print("Loading model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: "harm", 1: "safe"},
        label2id={"harm": 0, "safe": 1},
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        tokenizer=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving model to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("Training complete!")


if __name__ == "__main__":
    main()

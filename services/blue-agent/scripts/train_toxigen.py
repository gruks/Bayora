#!/usr/bin/env python3
"""Train a DistilBERT classifier on the ToxiGen dataset.

Usage:
    python train_toxigen.py --output-dir ./models/toxigen-classifier

This script fine-tunes distilbert-base-uncased on the ToxiGen dataset
for implicit toxicity detection. The ToxiGen dataset contains text labeled
as benign (0) or toxic (1), focusing on implicit toxicity that may evade
surface-level safety filters.

Note: Requires HuggingFace access approval for toxigen/toxigen-data.
Request access at: https://huggingface.co/datasets/toxigen/toxigen-data

Note: Requires GPU for reasonable training times. Use Google Colab if
local GPU unavailable.
"""

import argparse

from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


def _create_mock_dataset() -> Dataset:
    """Create a small mock dataset for testing the training pipeline.

    Used as fallback when HuggingFace dataset access is denied.
    """
    data = {
        "text": [
            "I hope you have a wonderful day ahead!",
            "The weather is nice today, isn't it?",
            "Let me help you with that task.",
            "Some groups of people are just inferior and deserve less.",
            "Those people always cause problems wherever they go.",
            "We should keep them away from our neighborhoods.",
        ],
        "label": [0, 0, 0, 1, 1, 1],
    }
    return Dataset.from_dict(data)


def main() -> None:
    """Train the ToxiGen classifier."""
    parser = argparse.ArgumentParser(
        description="Train a DistilBERT classifier on the ToxiGen dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./models/toxigen-classifier",
        help="Directory to save the fine-tuned model (default: ./models/toxigen-classifier)",
    )
    args = parser.parse_args()

    print("Loading ToxiGen dataset...")
    print("Note: Requires HuggingFace access approval for toxigen/toxigen-data.")
    print("Request access at: https://huggingface.co/datasets/toxigen/toxigen-data")

    try:
        dataset = load_dataset("toxigen/toxigen-data")
        train_ds = dataset["train"]
    except Exception:
        print(
            "WARNING: Could not access toxigen/toxigen-data dataset. "
            "Using mock dataset for pipeline testing."
        )
        full_ds = _create_mock_dataset()
        split = full_ds.train_test_split(test_size=0.2, seed=42)
        train_ds = split["train"]

    print(f"Dataset loaded: {len(train_ds)} training examples")
    print("ToxiGen format: text + label (0=benign, 1=toxic)")

    print("Tokenizing...")
    model_name = "distilbert/distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(examples: dict) -> dict:
        return tokenizer(examples["text"], truncation=True, max_length=512)

    tokenized = train_ds.map(tokenize, batched=True)
    split = tokenized if "test" in tokenized else tokenized.train_test_split(test_size=0.1, seed=42)

    print("Loading model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: "safe", 1: "harm"},
        label2id={"safe": 0, "harm": 1},
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
        train_dataset=split["train"],
        eval_dataset=split["test"],
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

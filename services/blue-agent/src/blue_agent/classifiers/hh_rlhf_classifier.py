"""HH-RLHF trained DistilBERT safety classifier.

Fine-tuned on Anthropic's HH-RLHF harmless-base dataset to classify
model responses as safe or harmful.
"""

from typing import Literal

from centinela.models.evaluation import ClassificationResult
from transformers import pipeline

from blue_agent.classifiers.base import SafetyClassifier

# Mapping from pipeline output labels to our classification labels
_LABEL_MAP: dict[str, Literal["safe", "harm"]] = {
    "LABEL_0": "harm",
    "LABEL_1": "safe",
}


class HHRLHFClassifier(SafetyClassifier):
    """Safety classifier trained on HH-RLHF harmless-base dataset.

    Uses a fine-tuned DistilBERT model for text classification.
    """

    def __init__(self, model_path: str, device: str = "cpu") -> None:
        """Initialize the HH-RLHF classifier.

        Args:
            model_path: Path to the fine-tuned model directory.
            device: Device to run inference on ("cpu" or "cuda").

        Raises:
            ValueError: If the model cannot be loaded from the given path.
        """
        try:
            self._pipeline = pipeline(
                "text-classification",
                model=model_path,
                tokenizer=model_path,
                device=device,
            )
        except Exception as e:
            raise ValueError(f"Failed to load HH-RLHF classifier from '{model_path}': {e}") from e

    def classify(self, response_text: str) -> ClassificationResult:
        """Classify a model response as safe or harmful.

        Args:
            response_text: The model's response text to classify.

        Returns:
            ClassificationResult with label, confidence, and model_source="hh_rlhf".
        """
        result = self._pipeline(response_text)[0]
        label = _LABEL_MAP.get(result["label"], "harm")
        confidence = result["score"]

        return ClassificationResult(
            label=label,
            confidence=confidence,
            model_source="hh_rlhf",
        )

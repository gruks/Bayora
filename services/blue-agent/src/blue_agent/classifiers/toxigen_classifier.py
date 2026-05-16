"""ToxiGen trained DistilBERT classifier for implicit toxicity detection.

Fine-tuned on the ToxiGen dataset to detect implicit toxicity in model
responses that may appear superficially safe but contain subtly harmful content.
"""

from typing import Literal

from centinela.models.evaluation import ClassificationResult
from transformers import pipeline  # type: ignore[attr-defined]

from blue_agent.classifiers.base import SafetyClassifier

# Mapping from pipeline output labels to our classification labels
_LABEL_MAP: dict[str, Literal["safe", "harm"]] = {
    "LABEL_0": "safe",
    "LABEL_1": "harm",
}


class ToxiGenClassifier(SafetyClassifier):
    """Safety classifier trained on the ToxiGen dataset.

    Uses a fine-tuned DistilBERT model for detecting implicit toxicity
    that may not be caught by general harmlessness classifiers.
    """

    def __init__(self, model_path: str, device: str = "cpu") -> None:
        """Initialize the ToxiGen classifier.

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
            raise ValueError(f"Failed to load ToxiGen classifier from '{model_path}': {e}") from e

    def classify(self, response_text: str) -> ClassificationResult:
        """Classify a model response for implicit toxicity.

        Args:
            response_text: The model's response text to classify.

        Returns:
            ClassificationResult with label, confidence, and model_source="toxigen".
        """
        result = self._pipeline(response_text)[0]
        label = _LABEL_MAP.get(result["label"], "harm")
        confidence = result["score"]

        return ClassificationResult(
            label=label,
            confidence=confidence,
            model_source="toxigen",
        )

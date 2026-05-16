"""Abstract safety classifier interface.

The original prompt is NEVER accessible — enforced by interface design (BLUE-04).
All classifiers implement classify(response_text) only.
"""

from abc import ABC, abstractmethod

from centinela.models.evaluation import ClassificationResult


class SafetyClassifier(ABC):
    """Abstract base class for safety classifiers.

    The interface accepts ONLY response_text — no prompt parameter.
    This enforces BLUE-04 at the type level: the original adversarial
    prompt is never accessible to the blue-agent evaluation system.
    """

    @abstractmethod
    def classify(self, response_text: str) -> ClassificationResult:
        """Classify a model response as safe or harmful.

        Args:
            response_text: The model's response text to classify.
                The original prompt is NOT available here.

        Returns:
            ClassificationResult with label, confidence, and model source.
        """
        ...

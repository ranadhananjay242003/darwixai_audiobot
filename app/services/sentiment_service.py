"""
Sentiment analysis service using HuggingFace Transformers.

Provides per-utterance sentiment classification (POSITIVE / NEGATIVE / NEUTRAL).
Lazy-loads the pipeline to avoid blocking startup.
"""

from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import SentimentAnalysisError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SentimentResult:
    """Result of sentiment analysis for a single text segment."""
    label: str  # POSITIVE | NEGATIVE | NEUTRAL
    score: float  # confidence 0.0 – 1.0


class SentimentService:
    """
    Sentiment analysis service backed by HuggingFace pipeline.

    Uses distilbert-base-uncased-finetuned-sst-2-english by default.
    """

    def __init__(self) -> None:
        self._pipeline = None
        self._settings = get_settings()

    def _load_pipeline(self) -> None:
        """Lazy-load the HuggingFace sentiment pipeline."""
        if self._pipeline is not None:
            return

        try:
            from transformers import pipeline as hf_pipeline

            model_name = self._settings.SENTIMENT_MODEL
            logger.info(f"Loading sentiment model: {model_name}")
            self._pipeline = hf_pipeline(
                "sentiment-analysis",
                model=model_name,
                truncation=True,
                max_length=512,
            )
            logger.info("Sentiment model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise SentimentAnalysisError(f"Model load failed: {e}") from e

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a single text string.

        Args:
            text: Input text to classify.

        Returns:
            SentimentResult with label and confidence score.
        """
        if not text or not text.strip():
            return SentimentResult(label="NEUTRAL", score=0.5)

        try:
            self._load_pipeline()
            result = self._pipeline(text[:512])[0]  # truncate input

            label = result["label"].upper()
            score = round(float(result["score"]), 4)

            return SentimentResult(label=label, score=score)

        except SentimentAnalysisError:
            raise
        except Exception as e:
            logger.warning(f"Sentiment analysis failed for text segment: {e}")
            return SentimentResult(label="NEUTRAL", score=0.0)

    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        """
        Analyze sentiment for a batch of texts.

        Args:
            texts: List of text strings.

        Returns:
            List of SentimentResult in the same order.
        """
        if not texts:
            return []

        try:
            self._load_pipeline()
            truncated = [t[:512] if t else "" for t in texts]
            results = self._pipeline(truncated)

            return [
                SentimentResult(
                    label=r["label"].upper(),
                    score=round(float(r["score"]), 4),
                )
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Batch sentiment analysis failed: {e}")
            return [SentimentResult(label="NEUTRAL", score=0.0) for _ in texts]


# ── Module-level singleton ───────────────────────────────────────────────
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Return the singleton sentiment service instance."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service

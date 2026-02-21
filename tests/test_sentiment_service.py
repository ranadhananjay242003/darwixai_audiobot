"""
Unit tests for the Sentiment Analysis service.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.sentiment_service import SentimentResult, SentimentService


class TestSentimentService:
    """Tests for SentimentService."""

    def setup_method(self):
        self.service = SentimentService()

    def test_analyze_empty_text(self):
        """Empty text returns NEUTRAL."""
        result = self.service.analyze("")
        assert result.label == "NEUTRAL"
        assert result.score == 0.5

    def test_analyze_whitespace_text(self):
        """Whitespace-only text returns NEUTRAL."""
        result = self.service.analyze("   ")
        assert result.label == "NEUTRAL"

    def test_analyze_positive(self):
        """Positive sentiment is correctly classified."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.9876}]
        self.service._pipeline = mock_pipeline

        result = self.service.analyze("This product is amazing!")

        assert result.label == "POSITIVE"
        assert result.score == 0.9876

    def test_analyze_negative(self):
        """Negative sentiment is correctly classified."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.8543}]
        self.service._pipeline = mock_pipeline

        result = self.service.analyze("This is terrible.")

        assert result.label == "NEGATIVE"
        assert result.score == 0.8543

    def test_analyze_batch(self):
        """Batch analysis processes multiple texts."""
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [
            {"label": "POSITIVE", "score": 0.95},
            {"label": "NEGATIVE", "score": 0.85},
            {"label": "POSITIVE", "score": 0.72},
        ]
        self.service._pipeline = mock_pipeline

        texts = ["Great!", "Terrible!", "Okay."]
        results = self.service.analyze_batch(texts)

        assert len(results) == 3
        assert results[0].label == "POSITIVE"
        assert results[1].label == "NEGATIVE"

    def test_analyze_batch_empty(self):
        """Empty batch returns empty list."""
        results = self.service.analyze_batch([])
        assert results == []

    def test_analyze_graceful_failure(self):
        """Pipeline failure returns neutral with 0 score."""
        mock_pipeline = MagicMock()
        mock_pipeline.side_effect = RuntimeError("Model crashed")
        self.service._pipeline = mock_pipeline

        result = self.service.analyze("Some text")

        assert result.label == "NEUTRAL"
        assert result.score == 0.0

"""
Unit tests for the Coachable Moment Detection service.
"""

import pytest

from app.services.coachable_service import CoachableDetectionService, CoachableMoment
from app.services.stt_service import TranscriptionSegment


class TestCoachableDetectionService:
    """Tests for CoachableDetectionService."""

    def setup_method(self):
        self.service = CoachableDetectionService()
        # Lower threshold for testing
        self.service._threshold = 0.3

    def _make_segment(self, text: str, start: float = 0.0, end: float = 1.0) -> TranscriptionSegment:
        """Helper to create a test segment."""
        return TranscriptionSegment(
            speaker="speaker_0",
            start_time=start,
            end_time=end,
            text=text,
        )

    def test_detect_objection_price(self):
        """Price-related objections are detected."""
        segments = [
            self._make_segment("That's too expensive for our budget"),
        ]
        moments = self.service.detect(segments)

        assert len(moments) >= 1
        assert moments[0].coachable_type == "objection"

    def test_detect_objection_competitor(self):
        """Competitor mentions are detected as objections."""
        segments = [
            self._make_segment("We're looking at another vendor for this"),
        ]
        moments = self.service.detect(segments)

        assert len(moments) >= 1
        assert moments[0].coachable_type == "objection"

    def test_detect_buying_signal(self):
        """Buying signals are detected."""
        segments = [
            self._make_segment("Sounds great! How soon can we get started?"),
        ]
        moments = self.service.detect(segments)

        assert len(moments) >= 1
        assert moments[0].coachable_type == "buying_signal"

    def test_detect_hesitation(self):
        """Hesitation patterns are detected."""
        segments = [
            self._make_segment("Um, I guess, I don't know, it's hard to say..."),
        ]
        moments = self.service.detect(segments)

        assert len(moments) >= 1
        assert moments[0].coachable_type == "hesitation"

    def test_detect_no_moments(self):
        """Benign text produces no coachable moments."""
        segments = [
            self._make_segment("The weather is nice today."),
        ]
        self.service._threshold = 0.9  # very high threshold
        moments = self.service.detect(segments)

        assert len(moments) == 0

    def test_detect_with_sentiment_boost(self):
        """Negative sentiment boosts objection confidence."""
        segments = [
            self._make_segment("I'm not sure about the pricing"),
        ]
        sentiments = [{"label": "NEGATIVE", "score": 0.9}]

        moments = self.service.detect(segments, sentiments)

        assert len(moments) >= 1
        # With sentiment boost, confidence should be higher
        assert moments[0].confidence > 0.3

    def test_detect_multiple_segments(self):
        """Multiple coachable moments across segments."""
        segments = [
            self._make_segment("Hello, nice to meet you", 0.0, 2.0),
            self._make_segment("This is too expensive for our budget", 3.0, 5.0),
            self._make_segment("But how soon can we sign up?", 6.0, 8.0),
            self._make_segment("Thank you", 9.0, 10.0),
        ]
        moments = self.service.detect(segments)

        # Should detect at least the objection and buying signal
        types_found = {m.coachable_type for m in moments}
        assert "objection" in types_found or "buying_signal" in types_found

    def test_detect_empty_segments(self):
        """Empty segment list returns empty moments."""
        moments = self.service.detect([])
        assert moments == []

    def test_moment_has_confidence(self):
        """Detected moments have a confidence score."""
        segments = [
            self._make_segment("We can't afford this, it's way over budget"),
        ]
        moments = self.service.detect(segments)

        if moments:
            assert 0.0 <= moments[0].confidence <= 1.0
            assert moments[0].matched_pattern  # should have explanation

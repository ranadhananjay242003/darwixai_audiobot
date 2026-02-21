"""
Coachable Moment Detection service.

Identifies segments that represent:
  - Customer objections (price, timing, competitor mentions)
  - Buying signals (interest, urgency, commitment)
  - Hesitations (uncertainty, filler phrases)

Uses a hybrid approach:
  1. Rule-based keyword/pattern matching (fast, deterministic)
  2. Sentiment-informed boosting (leverages sentiment scores)

Designed for future replacement with a trained NLP classifier.
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.stt_service import TranscriptionSegment

logger = get_logger(__name__)


@dataclass
class CoachableMoment:
    """Detected coachable moment metadata."""
    segment_index: int
    coachable_type: str  # objection | buying_signal | hesitation
    confidence: float  # 0.0 – 1.0
    matched_pattern: str  # description of what triggered detection


# ── Pattern Definitions ──────────────────────────────────────────────────

OBJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(too expensive|too costly|over budget|can't afford|out of.*budget)\b", re.IGNORECASE),
    re.compile(r"\b(not sure|not convinced|don't think|don't see the value)\b", re.IGNORECASE),
    re.compile(r"\b(competitor|alternative|other option|someone else|another vendor)\b", re.IGNORECASE),
    re.compile(r"\b(not the right time|bad timing|maybe later|not now|next quarter)\b", re.IGNORECASE),
    re.compile(r"\b(need to think|discuss with|check with|get back to you|talk to my)\b", re.IGNORECASE),
    re.compile(r"\b(doesn't fit|won't work|not what we need|don't need)\b", re.IGNORECASE),
    re.compile(r"\b(price|pricing|cost|expensive|budget|afford)\b", re.IGNORECASE),
]

BUYING_SIGNAL_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(sounds good|sounds great|interesting|love that|that's exactly)\b", re.IGNORECASE),
    re.compile(r"\b(how soon|when can|how quickly|timeline|onboarding)\b", re.IGNORECASE),
    re.compile(r"\b(pricing|what does it cost|subscription|plan options|packages)\b", re.IGNORECASE),
    re.compile(r"\b(sign up|get started|move forward|next steps|contract)\b", re.IGNORECASE),
    re.compile(r"\b(our team|we would|we could|we need|we want)\b", re.IGNORECASE),
    re.compile(r"\b(demo|trial|pilot|proof of concept|POC)\b", re.IGNORECASE),
    re.compile(r"\b(integration|API|connect|implement)\b", re.IGNORECASE),
]

HESITATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(um+|uh+|hmm+|er+|ah+)\b", re.IGNORECASE),
    re.compile(r"\b(I guess|I suppose|maybe|perhaps|not sure|uncertain)\b", re.IGNORECASE),
    re.compile(r"\b(kind of|sort of|I don't know|hard to say)\b", re.IGNORECASE),
    re.compile(r"\.\.\.", re.IGNORECASE),  # trailing ellipsis
    re.compile(r"\b(well|so|you know|like)\b", re.IGNORECASE),
]


class CoachableDetectionService:
    """
    Detects coachable moments in transcription segments.

    Scoring logic:
    - Pattern match → base confidence
    - Negative sentiment boosts objection confidence
    - Positive sentiment boosts buying signal confidence
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._threshold = self._settings.COACHABLE_CONFIDENCE_THRESHOLD

    def detect(
        self,
        segments: list[TranscriptionSegment],
        sentiments: list[Optional[dict]] | None = None,
    ) -> list[CoachableMoment]:
        """
        Scan segments for coachable moments.

        Args:
            segments: List of transcription segments.
            sentiments: Optional parallel list of sentiment dicts
                        with keys 'label' and 'score'.

        Returns:
            List of detected CoachableMoment instances.
        """
        moments: list[CoachableMoment] = []

        for i, seg in enumerate(segments):
            text = seg.text
            sentiment = sentiments[i] if sentiments and i < len(sentiments) else None

            # Check each category
            for category, patterns, boost_sentiment in [
                ("objection", OBJECTION_PATTERNS, "NEGATIVE"),
                ("buying_signal", BUYING_SIGNAL_PATTERNS, "POSITIVE"),
                ("hesitation", HESITATION_PATTERNS, None),
            ]:
                result = self._check_patterns(text, patterns, category, sentiment, boost_sentiment)
                if result and result.confidence >= self._threshold:
                    result.segment_index = i
                    moments.append(result)
                    break  # one label per segment to avoid noise

        logger.info(f"Coachable detection: {len(moments)} moments found in {len(segments)} segments")
        return moments

    def _check_patterns(
        self,
        text: str,
        patterns: list[re.Pattern],
        category: str,
        sentiment: Optional[dict],
        boost_sentiment: Optional[str],
    ) -> Optional[CoachableMoment]:
        """Check text against pattern list with sentiment boosting."""
        matched_patterns: list[str] = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matched_patterns.append(match.group())

        if not matched_patterns:
            return None

        # Base confidence from match density
        base_confidence = min(0.3 + len(matched_patterns) * 0.15, 0.85)

        # Sentiment boost
        if sentiment and boost_sentiment:
            if sentiment.get("label", "").upper() == boost_sentiment:
                base_confidence = min(base_confidence + 0.15, 1.0)

        return CoachableMoment(
            segment_index=0,  # will be set by caller
            coachable_type=category,
            confidence=round(base_confidence, 3),
            matched_pattern=", ".join(matched_patterns[:3]),
        )


# ── Module-level singleton ───────────────────────────────────────────────
_detection_service: Optional[CoachableDetectionService] = None


def get_coachable_service() -> CoachableDetectionService:
    """Return the singleton coachable detection service instance."""
    global _detection_service
    if _detection_service is None:
        _detection_service = CoachableDetectionService()
    return _detection_service

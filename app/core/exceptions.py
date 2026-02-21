"""
Application-specific exception hierarchy.

Provides typed exceptions that map to HTTP status codes,
keeping business logic decoupled from HTTP concerns.
"""


class DarwixBaseError(Exception):
    """Base error for all application exceptions."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AudioProcessingError(DarwixBaseError):
    """Raised when STT or audio pipeline fails."""

    def __init__(self, message: str = "Audio processing failed"):
        super().__init__(message=message, status_code=422)


class TranscriptionNotFoundError(DarwixBaseError):
    """Raised when a requested call/transcript is not found."""

    def __init__(self, call_id: str):
        super().__init__(message=f"Transcript not found for call_id={call_id}", status_code=404)


class TTSError(DarwixBaseError):
    """Raised when text-to-speech synthesis fails."""

    def __init__(self, message: str = "Text-to-speech synthesis failed"):
        super().__init__(message=message, status_code=500)


class SentimentAnalysisError(DarwixBaseError):
    """Raised when sentiment analysis fails (non-fatal, logged)."""

    def __init__(self, message: str = "Sentiment analysis failed"):
        super().__init__(message=message, status_code=500)


class ValidationError(DarwixBaseError):
    """Raised for business-level validation failures."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=400)

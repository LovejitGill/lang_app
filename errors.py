"""Shared expected errors and safe messages for the UI boundary."""


class SpeakWellError(RuntimeError):
    """Messages on these exceptions are deliberately written for the learner."""

    code = "APP_ERROR"


class LLMError(SpeakWellError):
    code = "TUTOR_ERROR"


class TutorUnavailable(LLMError):
    code = "TUTOR_UNAVAILABLE"


class LLMResponseError(LLMError):
    code = "TUTOR_INVALID_RESPONSE"


class StorageError(SpeakWellError):
    code = "HISTORY_UNAVAILABLE"


class TranscriptionError(SpeakWellError):
    code = "RECORDING_ERROR"


def user_message(error: Exception) -> str:
    """Known errors carry actionable text; unexpected errors must not leak data."""
    if isinstance(error, SpeakWellError):
        return f"{error.code}: {error}"
    if isinstance(error, ValueError):
        return str(error)
    return (
        "UNEXPECTED_ERROR: This action could not finish. Your draft may still be "
        "available. Try again; if it repeats, report which action failed."
    )

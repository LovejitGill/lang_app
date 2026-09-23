"""Error codes are stable; arbitrary internal exception messages stay private."""

from errors import TutorUnavailable, user_message


def test_actionable_error_code():
    assert (
        user_message(TutorUnavailable("Start Ollama"))
        == "TUTOR_UNAVAILABLE: Start Ollama"
    )


def test_unknown_exception_is_sanitized():
    message = user_message(RuntimeError("secret transcript"))
    assert "secret transcript" not in message
    assert message.startswith("UNEXPECTED_ERROR:")

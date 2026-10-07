import pytest

from speech_metrics import voice_latency, word_error_rate


def test_transcriber_fix_is_word_error():
    assert word_error_rate("She walk to work.", "She walks to work.")["wer"] == 0.25


def test_normalization():
    assert word_error_rate("Hello, WORLD!", "hello world")["wer"] == 0


def test_insertions_can_exceed_one():
    assert word_error_rate("Hi", "Hi how are you")["wer"] == 3


def test_empty_reference():
    with pytest.raises(ValueError):
        word_error_rate("", "hello")


def test_end_to_audio_not_first_token():
    values = {
        "speech_end": 1,
        "turn_detected": 1.3,
        "transcript_ready": 1.7,
        "first_token": 2,
        "first_audio": 3.5,
        "feedback_ready": 5,
    }
    result = voice_latency(values)
    assert result["speech_end_to_first_audio"] == 2.5
    assert result["speech_end_to_feedback"] == 4


def test_mixed_clock_rejected():
    with pytest.raises(ValueError):
        voice_latency(
            {
                "speech_end": 10,
                "turn_detected": 11,
                "transcript_ready": 1,
                "first_token": 2,
                "first_audio": 3,
            }
        )


def test_nonfinite_rejected():
    with pytest.raises(ValueError):
        voice_latency(
            {
                "speech_end": 0,
                "turn_detected": 1,
                "transcript_ready": 2,
                "first_token": 3,
                "first_audio": float("nan"),
            }
        )

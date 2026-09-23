"""Recording validation and failure paths; no downloads or real inference."""

import io
import wave
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

import stt


def recording(*, seconds=1, rate=16000, silent=False):
    count = int(seconds * rate)
    samples = np.zeros(count) if silent else np.sin(np.arange(count) * 0.08) * 3000
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.astype("<i2").tobytes())
    return buffer.getvalue()


@pytest.mark.parametrize("audio", [b"", b"not a wav", b"x" * (stt.MAX_BYTES + 1)])
def test_invalid_bytes_never_load_model(audio, monkeypatch):
    load = MagicMock()
    monkeypatch.setattr(stt, "get_model", load)
    with pytest.raises(stt.TranscriptionError):
        stt.transcribe_audio(audio)
    load.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"silent": True},
        {"seconds": 0.1},
        {"seconds": 61},
        {"rate": 44100},
    ],
)
def test_invalid_recordings(kwargs):
    with pytest.raises(stt.TranscriptionError):
        stt.decode_recording(recording(**kwargs))


def test_truncated_wav_rejected():
    with pytest.raises(stt.TranscriptionError, match="incomplete"):
        stt.decode_recording(recording()[:-2])


def test_lazy_segments_consumed_with_cpu_audio(monkeypatch):
    model = MagicMock()
    model.transcribe.return_value = (
        iter(
            [
                SimpleNamespace(
                    text=" I enjoy hiking. ", no_speech_prob=0.1, avg_logprob=-0.2
                )
            ]
        ),
        None,
    )
    monkeypatch.setattr(stt, "get_model", lambda: model)
    assert stt.transcribe_audio(recording()) == "I enjoy hiking."
    args, kwargs = model.transcribe.call_args
    assert args[0].dtype == np.float32
    assert len(args[0]) == 16000
    assert kwargs["vad_filter"] is True
    assert kwargs["language"] == "en"


@pytest.mark.parametrize(
    "segments",
    [
        [],
        [SimpleNamespace(text="noise", no_speech_prob=0.9, avg_logprob=-0.2)],
        [SimpleNamespace(text="uncertain", no_speech_prob=0.1, avg_logprob=-2)],
    ],
)
def test_no_clear_speech(monkeypatch, segments):
    model = MagicMock()
    model.transcribe.return_value = (iter(segments), None)
    monkeypatch.setattr(stt, "get_model", lambda: model)
    with pytest.raises(stt.TranscriptionError):
        stt.transcribe_audio(recording())


def test_lazy_runtime_failure_is_friendly(monkeypatch):
    def broken():
        raise RuntimeError("decoder failed")
        yield

    model = MagicMock()
    model.transcribe.return_value = (broken(), None)
    monkeypatch.setattr(stt, "get_model", lambda: model)
    with pytest.raises(stt.TranscriptionError, match="Local transcription failed"):
        stt.transcribe_audio(recording())


def test_missing_model_does_not_download(monkeypatch, tmp_path):
    stt.get_model.cache_clear()
    monkeypatch.setattr(stt, "MODEL_DIR", tmp_path)
    with pytest.raises(stt.TranscriptionError, match="Speech model missing"):
        stt.get_model()

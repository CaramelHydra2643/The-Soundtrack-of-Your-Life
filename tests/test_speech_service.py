import pytest

from modules.speech_service import SpeechService


def test_speech_rejects_unsupported_formats():
    with pytest.raises(ValueError, match="Unsupported audio format"):
        SpeechService().transcribe(b"audio", "recording.txt")


def test_speech_rejects_empty_recordings():
    with pytest.raises(ValueError, match="empty"):
        SpeechService().transcribe(b"", "recording.wav")

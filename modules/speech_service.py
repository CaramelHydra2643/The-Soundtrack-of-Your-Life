"""Optional local speech transcription using faster-whisper."""

import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SpeechService:
    """Transcribe short uploaded recordings without retaining the audio file."""

    SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}

    def __init__(self, model_size: str = "tiny", max_bytes: int = 25 * 1024 * 1024) -> None:
        self.model_size = model_size
        self.max_bytes = max_bytes
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "Speech transcription is optional. Install faster-whisper to enable it."
                ) from exc
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio: bytes, filename: str) -> dict[str, Any]:
        """Validate, transcribe, and immediately remove a temporary recording."""
        suffix = Path(filename or "").suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported audio format. Use WAV, MP3, M4A, WEBM, OGG, or FLAC.")
        if not audio:
            raise ValueError("The uploaded recording is empty.")
        if len(audio) > self.max_bytes:
            raise ValueError("The recording is too large. Keep recordings under 25 MB.")

        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                handle.write(audio)
                temporary_path = handle.name
            segments, info = self._get_model().transcribe(
                temporary_path, beam_size=1, vad_filter=True
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {
                "transcription": text,
                "language": getattr(info, "language", None),
                "duration": float(getattr(info, "duration", 0.0) or 0.0),
                "status": "completed",
            }
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Speech transcription failed: %s", exc)
            raise RuntimeError("The recording could not be transcribed.") from exc
        finally:
            if temporary_path:
                try:
                    Path(temporary_path).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove temporary audio file")

"""FastAPI service boundary for The Soundtrack of Your Life.

Run with `uvicorn api:app --reload` after installing the API dependencies.
"""

from functools import lru_cache

from pydantic import BaseModel, Field

try:
    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as exc:  # pragma: no cover - gives a useful setup error
    raise RuntimeError(
        "FastAPI is not installed. Run `pip install -r requirements.txt`."
    ) from exc

from modules.soundtrack_service import SoundtrackService
from modules.speech_service import SpeechService
from schemas.memory_schema import SoundtrackResult

app = FastAPI(
    title="The Soundtrack of Your Life API",
    version="0.1.0",
    description="Local-first memory analysis and soundtrack recommendation API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


class MemoryRequest(BaseModel):
    """Validated memory submission payload."""

    memory: str = Field(..., min_length=10, max_length=5000)


class SaveRequest(MemoryRequest):
    """Memory payload used when persisting an already generated result."""

    result: SoundtrackResult


class RefineRequest(SaveRequest):
    """Existing soundtrack plus a bounded refinement instruction."""

    instruction: str = Field(..., min_length=3, max_length=300)


class FeedbackRequest(BaseModel):
    """Validated user reaction to one recommendation."""

    track_id: str = Field(..., min_length=1, max_length=200)
    feedback_type: str = Field(..., pattern="^(like|dislike|save|skip)$")
    memory_id: int | None = Field(default=None, ge=1)


class PreferencesRequest(BaseModel):
    """Single-user recommendation preferences."""

    preferred_languages: list[str] = Field(default_factory=list, max_length=30)
    preferred_genres: list[str] = Field(default_factory=list, max_length=50)
    disliked_genres: list[str] = Field(default_factory=list, max_length=50)
    preferred_eras: list[str] = Field(default_factory=list, max_length=20)
    regional_preferences: list[str] = Field(default_factory=list, max_length=30)
    explicit_content: str = Field(default="allow", pattern="^(allow|avoid|unknown)$")
    diversity: float = Field(default=0.5, ge=0.0, le=1.0)


@lru_cache(maxsize=1)
def get_service() -> SoundtrackService:
    """Initialize expensive local models once per API process."""
    return SoundtrackService()


@lru_cache(maxsize=1)
def get_speech_service() -> SpeechService:
    """Cache the optional local Whisper model after the first transcription."""
    return SpeechService()


@lru_cache(maxsize=1)
def get_vault():
    """Initialize SQLite-only endpoints without loading embedding models."""
    from modules.memory_vault import MemoryVault
    return MemoryVault()


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return a lightweight process health response without loading models."""
    return {"status": "ok", "mode": "local"}


@app.post("/api/speech/transcribe")
async def transcribe_speech(file: UploadFile = File(...)) -> dict:
    """Transcribe one recording and discard its temporary server-side copy."""
    try:
        audio = await file.read()
        return get_speech_service().transcribe(audio, file.filename or "recording.wav")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/soundtracks", response_model=SoundtrackResult)
def generate_soundtrack(request: MemoryRequest) -> SoundtrackResult:
    """Analyze a memory and return grounded recommendations."""
    try:
        return get_service().generate(request.memory)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/soundtracks/refine", response_model=SoundtrackResult)
def refine_soundtrack(request: RefineRequest) -> SoundtrackResult:
    """Apply a conversational refinement to an existing soundtrack."""
    try:
        return get_service().refine(request.memory, request.result, request.instruction)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/memories", response_model=dict[str, int])
def save_memory(request: SaveRequest) -> dict[str, int]:
    """Persist a soundtrack after the client explicitly requests saving."""
    try:
        memory_id = get_vault().save_memory(request.memory.strip(), request.result)
        if memory_id is None:
            raise RuntimeError("The soundtrack could not be saved.")
        return {"memory_id": memory_id}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/feedback", response_model=dict[str, bool])
def record_feedback(request: FeedbackRequest) -> dict[str, bool]:
    """Persist a like, dislike, save, or skip action."""
    if not get_vault().record_feedback(
        request.track_id, request.feedback_type, request.memory_id
    ):
        raise HTTPException(status_code=422, detail="Feedback could not be recorded")
    return {"recorded": True}


@app.get("/api/feedback")
def list_feedback() -> list[dict]:
    """Return recent feedback without returning raw memories."""
    return get_vault().get_feedback()


@app.get("/api/preferences")
def get_preferences() -> dict:
    """Return current recommendation preferences."""
    return get_vault().get_preferences()


@app.put("/api/preferences")
def update_preferences(request: PreferencesRequest) -> dict[str, bool]:
    """Persist recommendation preferences for local single-user mode."""
    if not get_vault().save_preferences(request.model_dump()):
        raise HTTPException(status_code=422, detail="Preferences could not be saved")
    return {"saved": True}


@app.get("/api/export")
def export_data() -> dict:
    """Export all local user data in a JSON-safe response."""
    return get_vault().export_data()


@app.delete("/api/data", response_model=dict[str, bool])
def delete_all_data() -> dict[str, bool]:
    """Delete all memories, feedback, and preferences."""
    if not get_vault().delete_all_data():
        raise HTTPException(status_code=503, detail="Personal data could not be deleted")
    return {"deleted": True}


@app.get("/api/memories")
def list_memories() -> list[dict]:
    """Return saved local memories for the single-user local mode."""
    return get_vault().get_all_memories()


@app.delete("/api/memories/{memory_id}", response_model=dict[str, bool])
def delete_memory(memory_id: int) -> dict[str, bool]:
    """Delete one local memory by id."""
    if memory_id < 1:
        raise HTTPException(status_code=422, detail="memory_id must be positive")
    deleted = get_vault().delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}

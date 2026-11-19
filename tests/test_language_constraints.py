from config.settings import Settings
from modules.music_catalogue import MusicCatalogue
from modules.recommendation_engine import RecommendationEngine
from schemas.memory_schema import MemoryAnalysis


def test_explicit_requested_music_language_is_hard_constraint():
    analysis = MemoryAnalysis(
        memory_title="A Telugu memory",
        summary="A meaningful memory with a clear musical direction.",
        primary_emotions=["nostalgia"],
        secondary_emotions=[],
        emotional_intensity=5,
        themes=["family"],
        context=[],
        genres=["folk"],
        instruments=["piano"],
        tempo="moderate",
        energy="low",
        atmosphere="warm and reflective",
        musical_description="Warm reflective music for a family memory.",
        language="English",
        requested_music_language="Telugu",
    )
    catalogue = object.__new__(MusicCatalogue)
    catalogue.tracks = [
        {"track_id": "en", "track_name": "English Track", "artist": "A", "language": "English", "genre_tags": ["folk"], "mood_tags": ["nostalgia"], "instrument_tags": ["piano"]},
        {"track_id": "te", "track_name": "Telugu Track", "artist": "B", "language": "Telugu", "genre_tags": ["folk"], "mood_tags": ["nostalgia"], "instrument_tags": ["piano"]},
    ]
    catalogue.settings = Settings(app_data_dir=".test-data")
    result = RecommendationEngine(catalogue).generate_recommendations(analysis)
    assert result
    assert all(item.language == "Telugu" for item in result)

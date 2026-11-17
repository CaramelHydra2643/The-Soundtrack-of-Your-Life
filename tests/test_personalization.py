from config.settings import Settings
from modules.music_catalogue import MusicCatalogue
from modules.recommendation_engine import RecommendationEngine
from schemas.memory_schema import MemoryAnalysis


def test_disliked_genre_is_excluded():
    analysis = MemoryAnalysis(
        memory_title="A memory", summary="A meaningful memory with a clear musical direction.",
        primary_emotions=["joy"], secondary_emotions=[], emotional_intensity=5,
        themes=["celebration"], context=[], genres=["pop"], instruments=["piano"],
        tempo="moderate", energy="high", atmosphere="bright and joyful",
        musical_description="Bright piano-led music for a celebratory memory.",
    )
    catalogue = object.__new__(MusicCatalogue)
    catalogue.tracks = [
        {"track_id": "pop", "track_name": "Bright", "artist": "A", "genre_tags": ["pop"], "mood_tags": ["joy"], "instrument_tags": ["piano"]},
        {"track_id": "folk", "track_name": "Open Sky", "artist": "B", "genre_tags": ["folk"], "mood_tags": ["joy"], "instrument_tags": ["piano"]},
    ]
    catalogue.settings = Settings(app_data_dir=".test-data")
    result = RecommendationEngine(catalogue).generate_recommendations(
        analysis, user_preferences={"disliked_genres": ["pop"]}
    )
    assert result
    assert all("pop" not in item.genre_tags for item in result)

from modules.recommendation_engine import RecommendationEngine
from schemas.memory_schema import MemoryAnalysis


def test_numeric_audio_features_are_used_without_breaking_missing_data():
    analysis = MemoryAnalysis(
        memory_title="A joyful memory",
        summary="A joyful memory with celebration and warmth",
        primary_emotions=["happiness"],
        secondary_emotions=[],
        emotional_intensity=7,
        themes=["celebration"],
        context=[],
        genres=["pop"],
        instruments=["piano"],
        tempo="moderate",
        energy="moderate",
        atmosphere="warm and joyful",
        musical_description="An uplifting and joyful musical direction",
        language="English",
        cultural_context=[],
    )
    engine = object.__new__(RecommendationEngine)
    strong = engine._audio_compatibility({"energy": 0.55, "tempo": 110, "valence": 0.7}, analysis)
    missing = engine._audio_compatibility({}, analysis)
    assert strong > missing
    assert 0.0 <= strong <= 1.0

from config.settings import Settings
from modules.music_catalogue import MusicCatalogue
from modules.recommendation_engine import RecommendationEngine
from schemas.memory_schema import MemoryAnalysis


def analysis(**overrides):
    payload = {
        "memory_title": "A warm memory",
        "summary": "A remembered moment filled with family warmth and nostalgia.",
        "primary_emotions": ["nostalgia"],
        "secondary_emotions": ["warmth"],
        "emotional_intensity": 7,
        "themes": ["family", "belonging"],
        "context": ["childhood"],
        "genres": ["indie folk"],
        "instruments": ["acoustic guitar"],
        "tempo": "slow",
        "energy": "low",
        "atmosphere": "warm and reflective",
        "musical_description": "Gentle acoustic textures with a reflective, comforting character.",
    }
    payload.update(overrides)
    return MemoryAnalysis(**payload)


def catalogue_with_tracks(tracks):
    catalogue = object.__new__(MusicCatalogue)
    catalogue.tracks = tracks
    catalogue.catalogue_df = None
    catalogue.settings = Settings(app_data_dir=".test-data")
    return catalogue


def test_rag_context_changes_ranking():
    tracks = [
        {
            "track_id": "folk", "track_name": "Family Porch", "artist": "North Star",
            "genre_tags": ["indie folk"], "mood_tags": ["nostalgia"],
            "instrument_tags": ["acoustic guitar"], "themes": ["family"], "language": "English",
        },
        {
            "track_id": "ambient", "track_name": "Quiet Room", "artist": "Still Water",
            "genre_tags": ["ambient"], "mood_tags": ["peaceful"],
            "instrument_tags": ["piano"], "themes": ["solitude"], "language": "English",
        },
    ]
    engine = RecommendationEngine(catalogue_with_tracks(tracks))
    baseline = engine.generate_recommendations(analysis(), retrieved_context=[])
    rag = engine.generate_recommendations(
        analysis(genres=["ambient"], instruments=["piano"], primary_emotions=["peaceful"]),
        retrieved_context=[{
            "text": "Ambient music supports quiet reflection and peaceful solitude.",
            "metadata": {"category": "genre", "topic": "Ambient"}, "relevance_score": 0.95,
        }],
    )
    assert baseline[0].track_id == "folk"
    assert rag[0].track_id == "ambient"


def test_missing_metadata_does_not_crash_or_create_out_of_range_scores():
    engine = RecommendationEngine(catalogue_with_tracks([
        {"track_id": "minimal", "track_name": "Unknown", "artist": "Unknown"}
    ]))
    assert engine.generate_recommendations(analysis(), retrieved_context=[]) == []


def test_recommendations_are_diverse_by_artist():
    tracks = [
        {
            "track_id": str(index), "track_name": f"Track {index}",
            "artist": "Same Artist" if index < 3 else "Different Artist",
            "genre_tags": ["indie folk"], "mood_tags": ["nostalgia"],
            "instrument_tags": ["acoustic guitar"], "themes": ["family"],
        }
        for index in range(4)
    ]
    recommendations = RecommendationEngine(catalogue_with_tracks(tracks)).generate_recommendations(
        analysis(), max_recommendations=3
    )
    assert len({item.artist for item in recommendations}) >= 2

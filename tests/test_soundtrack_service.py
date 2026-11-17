import pytest

from modules.soundtrack_service import SoundtrackService
from schemas.memory_schema import MemoryAnalysis, TrackRecommendation


class FakeAnalyzer:
    def analyze_memory(self, memory):
        return MemoryAnalysis(
            memory_title="A remembered day",
            summary="A warm remembered day with a hopeful ending.",
            primary_emotions=["hope"],
            secondary_emotions=["warmth"],
            emotional_intensity=6,
            themes=["growth"],
            context=["home"],
            genres=["folk"],
            instruments=["piano"],
            tempo="moderate",
            energy="moderate",
            atmosphere="warm and hopeful",
            musical_description="Gentle folk textures with a hopeful, human quality.",
        )

    def create_retrieval_query(self, analysis):
        return "hope growth folk"


class FakeRag:
    def is_knowledge_base_ready(self):
        return True

    def retrieve(self, query):
        return [{"text": "Hopeful folk music", "metadata": {"topic": "Folk"}, "relevance_score": 0.9}]

    def get_retrieval_summary(self, docs):
        return ["genre: Folk"]


class FakeRecommender:
    def generate_recommendations(self, analysis, retrieved):
        return [TrackRecommendation(
            track_id="demo",
            track_name="A New Page",
            artist="Open Roads",
            genre_tags=["folk"],
            mood_tags=["hope"],
            instrument_tags=["piano"],
            relevance_score=0.8,
            explanation="Its hopeful folk texture matches the memory.",
        )]


class FakeExplainer:
    def generate_overall_explanation(self, memory, analysis, recommendations, retrieved):
        return "A hopeful soundtrack for a memory about growth and home." * 2


class FakeVault:
    def save_memory(self, memory, result):
        return 7


def service():
    return SoundtrackService(
        analyzer=FakeAnalyzer(),
        rag_engine=FakeRag(),
        recommender=FakeRecommender(),
        explainer=FakeExplainer(),
        vault=FakeVault(),
        catalogue=object(),
    )


def test_service_composes_domain_steps_and_preserves_context():
    result = service().generate("I remember returning home after a difficult year.")
    assert result.recommendations[0].track_id == "demo"
    assert result.retrieved_knowledge_summary == ["genre: Folk"]


def test_service_rejects_short_memory_before_model_work():
    with pytest.raises(ValueError, match="at least 10"):
        service().generate("too short")


def test_service_save_requires_explicit_call():
    result = service().generate("I remember returning home after a difficult year.")
    assert service().save("I remember returning home after a difficult year.", result) == 7

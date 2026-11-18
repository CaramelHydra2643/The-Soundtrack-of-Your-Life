import pytest

from modules.soundtrack_service import SoundtrackService
from test_soundtrack_service import FakeAnalyzer, FakeExplainer, FakeRag, FakeRecommender, FakeVault


def build_service():
    return SoundtrackService(
        analyzer=FakeAnalyzer(), rag_engine=FakeRag(), recommender=FakeRecommender(),
        explainer=FakeExplainer(), vault=FakeVault(), catalogue=object(),
    )


def test_memory_analysis_accepts_single_cultural_context_sentence():
    from schemas.memory_schema import MemoryAnalysis

    analysis = MemoryAnalysis(
        memory_title="A memory", summary="A meaningful memory with enough detail to validate.",
        primary_emotions=["warmth"], secondary_emotions=[], emotional_intensity=5,
        themes=["family"], context=["home"], genres=["folk"], instruments=["piano"],
        tempo="slow", energy="low", atmosphere="warm and reflective",
        musical_description="Gentle music with a warm reflective character.",
        cultural_context="A regional family gathering.",
    )
    assert analysis.cultural_context == ["A regional family gathering."]


def test_refinement_updates_supported_emotional_direction():
    service = build_service()
    original = service.generate("I remember returning home after a difficult year.")
    refined = service.refine("I remember returning home after a difficult year.", original, "make it more nostalgic")
    assert "nostalgia" in refined.memory_analysis.primary_emotions
    assert refined.recommendations


def test_refinement_rejects_unsupported_instruction():
    service = build_service()
    original = service.generate("I remember returning home after a difficult year.")
    with pytest.raises(ValueError, match="nostalgic"):
        service.refine("I remember returning home after a difficult year.", original, "do something random")

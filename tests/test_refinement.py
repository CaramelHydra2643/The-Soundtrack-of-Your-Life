import pytest

from modules.soundtrack_service import SoundtrackService
from test_soundtrack_service import FakeAnalyzer, FakeExplainer, FakeRag, FakeRecommender, FakeVault


def build_service():
    return SoundtrackService(
        analyzer=FakeAnalyzer(), rag_engine=FakeRag(), recommender=FakeRecommender(),
        explainer=FakeExplainer(), vault=FakeVault(), catalogue=object(),
    )


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

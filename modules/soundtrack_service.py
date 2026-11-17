"""Application orchestration for generating and saving personal soundtracks."""

import inspect
import logging
from typing import Optional

from config.settings import get_settings
from modules.explanation_generator import ExplanationGenerator
from modules.memory_analyzer import MemoryAnalyzer
from modules.memory_vault import MemoryVault
from modules.music_catalogue import MusicCatalogue
from modules.rag_engine import RAGEngine
from modules.recommendation_engine import RecommendationEngine
from schemas.memory_schema import SoundtrackResult

logger = logging.getLogger(__name__)


class SoundtrackService:
    """Coordinates domain services without coupling them to Streamlit or HTTP."""

    def __init__(
        self,
        analyzer: Optional[MemoryAnalyzer] = None,
        rag_engine: Optional[RAGEngine] = None,
        catalogue: Optional[MusicCatalogue] = None,
        recommender: Optional[RecommendationEngine] = None,
        explainer: Optional[ExplanationGenerator] = None,
        vault: Optional[MemoryVault] = None,
    ) -> None:
        self.settings = get_settings()
        self.analyzer = analyzer or MemoryAnalyzer()
        self.rag_engine = rag_engine or RAGEngine()
        self.catalogue = catalogue or MusicCatalogue()
        self.recommender = recommender or RecommendationEngine(self.catalogue)
        self.explainer = explainer or ExplanationGenerator()
        self.vault = vault or MemoryVault()

    def generate(self, memory_text: str) -> SoundtrackResult:
        """Generate a validated soundtrack result from one memory."""
        normalized = (memory_text or "").strip()
        if len(normalized) < 10:
            raise ValueError("Memory must contain at least 10 characters.")
        if len(normalized) > self.settings.max_memory_length:
            raise ValueError(
                f"Memory must be no longer than {self.settings.max_memory_length} characters."
            )

        analysis = self.analyzer.analyze_memory(normalized)
        if analysis is None:
            raise RuntimeError("Memory analysis failed. Check the local Ollama model and try again.")

        retrieved = []
        if self.rag_engine.is_knowledge_base_ready():
            query = self.analyzer.create_retrieval_query(analysis)
            retrieved = self.rag_engine.retrieve(query)

        get_preferences = getattr(self.vault, "get_preferences", lambda: {})
        get_feedback = getattr(self.vault, "get_feedback", lambda: [])
        preferences = get_preferences()
        preferences["feedback"] = get_feedback()
        recommender_params = inspect.signature(
            self.recommender.generate_recommendations
        ).parameters
        if "user_preferences" in recommender_params:
            recommendations = self.recommender.generate_recommendations(
                analysis, retrieved, user_preferences=preferences
            )
        else:
            recommendations = self.recommender.generate_recommendations(analysis, retrieved)
        if not recommendations:
            raise RuntimeError("No catalogue tracks matched this memory.")

        explanation = self.explainer.generate_overall_explanation(
            normalized, analysis, recommendations, retrieved
        )
        return SoundtrackResult(
            memory_analysis=analysis,
            recommendations=recommendations,
            overall_explanation=explanation,
            retrieved_knowledge_summary=(
                self.rag_engine.get_retrieval_summary(retrieved) if retrieved else None
            ),
        )

    def refine(
        self,
        memory_text: str,
        result: SoundtrackResult,
        instruction: str,
    ) -> SoundtrackResult:
        """Apply a bounded natural-language refinement to an existing soundtrack."""
        request = (instruction or "").strip().lower()
        if len(request) < 3 or len(request) > 300:
            raise ValueError("Refinement must be between 3 and 300 characters.")

        analysis = result.memory_analysis.model_copy(deep=True)
        recognized = False
        if any(term in request for term in ("nostalgic", "nostalgia", "bittersweet")):
            analysis.primary_emotions = list(dict.fromkeys(analysis.primary_emotions + ["nostalgia"]))
            analysis.themes = list(dict.fromkeys(analysis.themes + ["memory", "reflection"]))
            analysis.genres = list(dict.fromkeys(["indie folk", "acoustic pop"] + analysis.genres))
            recognized = True
        if any(term in request for term in ("peaceful", "calm", "quiet", "serene")):
            analysis.primary_emotions = list(dict.fromkeys(analysis.primary_emotions + ["peace"]))
            analysis.genres = list(dict.fromkeys(["ambient", "classical"] + analysis.genres))
            analysis.tempo = "slow"
            analysis.energy = "low"
            recognized = True
        if any(term in request for term in ("energetic", "upbeat", "exciting", "dance")):
            analysis.primary_emotions = list(dict.fromkeys(analysis.primary_emotions + ["excitement"]))
            analysis.genres = list(dict.fromkeys(["indie pop", "pop"] + analysis.genres))
            analysis.tempo = "fast"
            analysis.energy = "high"
            recognized = True
        for language in ("telugu", "tamil", "hindi", "kannada", "malayalam", "bengali", "punjabi", "english"):
            if language in request:
                analysis.language = language.title()
                recognized = True
                break
        if not recognized:
            raise ValueError("Try asking for something more nostalgic, peaceful, energetic, or a specific language.")

        retrieved = []
        if self.rag_engine.is_knowledge_base_ready():
            retrieved = self.rag_engine.retrieve(self.analyzer.create_retrieval_query(analysis))
        get_preferences = getattr(self.vault, "get_preferences", lambda: {})
        get_feedback = getattr(self.vault, "get_feedback", lambda: [])
        preferences = get_preferences()
        preferences["feedback"] = get_feedback()
        params = inspect.signature(self.recommender.generate_recommendations).parameters
        if "user_preferences" in params:
            recommendations = self.recommender.generate_recommendations(analysis, retrieved, user_preferences=preferences)
        else:
            recommendations = self.recommender.generate_recommendations(analysis, retrieved)
        if not recommendations:
            raise RuntimeError("No tracks matched that refinement.")
        explanation = self.explainer.generate_overall_explanation(memory_text, analysis, recommendations, retrieved)
        return SoundtrackResult(
            memory_analysis=analysis,
            recommendations=recommendations,
            overall_explanation=explanation,
            retrieved_knowledge_summary=(self.rag_engine.get_retrieval_summary(retrieved) if retrieved else None),
        )

    def save(self, memory_text: str, result: SoundtrackResult) -> int:
        """Persist a result only after an explicit user save action."""
        memory_id = self.vault.save_memory(memory_text.strip(), result)
        if memory_id is None:
            raise RuntimeError("The soundtrack could not be saved.")
        return memory_id

"""
Explanation Generator

Generates natural language explanations for soundtrack recommendations using LLM.
"""

import logging
from typing import List, Dict, Any, Optional

import ollama

from config.settings import get_settings
from schemas.memory_schema import MemoryAnalysis, TrackRecommendation

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """Generates explanations for music recommendations using LLM."""

    def __init__(self):
        """Initialize explanation generator."""
        self.settings = get_settings()
        self.model = self.settings.ollama_model
        self.temperature = self.settings.llm_temperature
        self.client = ollama.Client(host=self.settings.ollama_base_url)

    def generate_overall_explanation(
        self,
        memory_text: str,
        analysis: MemoryAnalysis,
        recommendations: List[TrackRecommendation],
        retrieved_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate overall explanation for the soundtrack.
        
        Args:
            memory_text: Original memory text
            analysis: Memory analysis results
            recommendations: List of track recommendations
            retrieved_context: RAG retrieved knowledge
            
        Returns:
            Overall explanation string
        """
        if not self.settings.enable_llm_explanations:
            return self._create_fallback_overall_explanation(analysis, recommendations)

        # Build context from RAG retrieval
        rag_context = ""
        if retrieved_context:
            context_snippets = []
            for doc in retrieved_context[:3]:  # Use top 3
                metadata = doc.get('metadata', {})
                topic = metadata.get('topic', 'unknown')
                context_snippets.append(f"- {topic}")
            
            if context_snippets:
                rag_context = "\nRelevant music knowledge considered:\n" + "\n".join(context_snippets)
        
        # Build track list
        track_list = "\n".join([
            f"{i+1}. {rec.track_name} by {rec.artist}"
            for i, rec in enumerate(recommendations[:5])
        ])
        
        prompt = f"""You are a music curator explaining why specific tracks were selected for someone's personal memory.

MEMORY:
\"\"\"
{memory_text}
\"\"\"

EMOTIONAL ANALYSIS:
- Primary emotions: {', '.join(analysis.primary_emotions)}
- Themes: {', '.join(analysis.themes)}
- Atmosphere: {analysis.atmosphere}

RECOMMENDED TRACKS:
{track_list}
{rag_context}

Write a warm, personal explanation (100-150 words) of why this soundtrack was curated for this memory. 
Focus on the emotional and musical connections. Be genuine and empathetic.

Do not mention technical details like "algorithms" or "scoring". Write as a human curator would.
"""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': min(self.temperature + 0.2, 2.0)}
            )
            
            explanation = response['message']['content'].strip()
            logger.info("Generated overall explanation")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate overall explanation: {e}")
            # Fallback explanation
            return self._create_fallback_overall_explanation(analysis, recommendations)

    def _create_fallback_overall_explanation(
        self,
        analysis: MemoryAnalysis,
        recommendations: List[TrackRecommendation]
    ) -> str:
        """Create fallback explanation without LLM.
        
        Args:
            analysis: Memory analysis
            recommendations: Track recommendations
            
        Returns:
            Fallback explanation
        """
        emotions_str = ", ".join(analysis.primary_emotions[:2])
        num_tracks = len(recommendations)
        
        explanation = (
            f"This soundtrack of {num_tracks} tracks captures the {emotions_str} "
            f"emotions in your memory. The selection focuses on {', '.join(analysis.genres[:2])} "
            f"music with {analysis.atmosphere} atmosphere, featuring {', '.join(analysis.instruments[:2])} "
            f"to reflect the emotional depth of your experience."
        )
        
        return explanation

    def enhance_track_explanation(
        self,
        track: TrackRecommendation,
        analysis: MemoryAnalysis,
        retrieved_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Enhance a track's explanation using LLM (optional, for detailed view).
        
        Args:
            track: Track recommendation
            analysis: Memory analysis
            retrieved_context: RAG context
            
        Returns:
            Enhanced explanation
        """
        # For now, return the existing explanation
        # This can be enhanced with LLM calls for individual tracks if needed
        return track.explanation

    def create_rag_transparency_summary(
        self,
        retrieved_context: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        """Create human-readable summary of RAG retrieval for transparency.
        
        Args:
            retrieved_context: Retrieved documents from RAG
            
        Returns:
            List of summary strings
        """
        if not retrieved_context:
            return ["No music knowledge retrieved"]
        
        summaries = []
        for doc in retrieved_context[:5]:  # Show top 5
            metadata = doc.get('metadata', {})
            category = metadata.get('category', 'unknown')
            topic = metadata.get('topic', 'unknown')
            relevance = doc.get('relevance_score', 0.0)
            
            summary = f"{category.capitalize()}: {topic} (relevance: {relevance:.0%})"
            summaries.append(summary)
        
        return summaries

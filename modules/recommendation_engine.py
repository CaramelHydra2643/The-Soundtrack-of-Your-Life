"""
Recommendation Engine

Combines memory analysis, RAG retrieval, and music catalogue to generate recommendations.
"""

import logging
from typing import List, Dict, Any, Optional, Set

from config.settings import get_settings
from schemas.memory_schema import MemoryAnalysis, TrackRecommendation
from modules.music_catalogue import MusicCatalogue

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates music recommendations based on memory analysis and RAG context."""

    def __init__(self, catalogue: Optional[MusicCatalogue] = None):
        """Initialize recommendation engine.
        
        Args:
            catalogue: Music catalogue instance (creates new if None)
        """
        self.settings = get_settings()
        self.catalogue = catalogue or MusicCatalogue()

    def _calculate_tag_overlap(
        self,
        search_tags: List[str],
        track_tags: List[str]
    ) -> float:
        """Calculate overlap score between search and track tags.
        
        Args:
            search_tags: Tags from memory analysis
            track_tags: Tags from track metadata
            
        Returns:
            Overlap score between 0 and 1
        """
        if not search_tags or not track_tags:
            return 0.0
        
        # Normalize to lowercase for comparison
        search_set = set([t.lower().strip() for t in search_tags if t])
        track_set = set([t.lower().strip() for t in track_tags if t])
        
        if not search_set:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(search_set.intersection(track_set))
        union = len(search_set.union(track_set))
        
        if union == 0:
            return 0.0
        
        return intersection / union

    def _score_track(
        self,
        track: Dict[str, Any],
        analysis: MemoryAnalysis
    ) -> float:
        """Score a track's relevance to the memory analysis.
        
        Args:
            track: Track metadata dictionary
            analysis: Memory analysis results
            
        Returns:
            Relevance score between 0 and 1
        """
        # Combine all emotions
        all_emotions = analysis.primary_emotions + analysis.secondary_emotions
        
        # Calculate component scores
        mood_score = self._calculate_tag_overlap(
            all_emotions + analysis.themes,
            track.get('mood_tags', [])
        )
        
        genre_score = self._calculate_tag_overlap(
            analysis.genres,
            track.get('genre_tags', [])
        )
        
        instrument_score = self._calculate_tag_overlap(
            analysis.instruments,
            track.get('instrument_tags', [])
        )
        
        # Theme matching (use context and themes)
        theme_score = self._calculate_tag_overlap(
            analysis.context + analysis.themes,
            track.get('mood_tags', []) + track.get('genre_tags', [])
        )
        
        # Weighted final score using configured weights
        final_score = (
            self.settings.weight_mood * mood_score +
            self.settings.weight_genre * genre_score +
            self.settings.weight_instrument * instrument_score +
            self.settings.weight_theme * theme_score
        )
        
        logger.debug(
            f"Track: {track.get('track_name')}, "
            f"Mood: {mood_score:.2f}, Genre: {genre_score:.2f}, "
            f"Instrument: {instrument_score:.2f}, Theme: {theme_score:.2f}, "
            f"Final: {final_score:.2f}"
        )
        
        return final_score

    def generate_recommendations(
        self,
        analysis: MemoryAnalysis,
        retrieved_context: Optional[List[Dict[str, Any]]] = None,
        max_recommendations: Optional[int] = None
    ) -> List[TrackRecommendation]:
        """Generate track recommendations.
        
        Args:
            analysis: Memory analysis results
            retrieved_context: RAG retrieved knowledge (for transparency)
            max_recommendations: Maximum recommendations to return
            
        Returns:
            List of TrackRecommendation objects
        """
        max_recommendations = max_recommendations or self.settings.max_recommendations
        
        logger.info("Generating track recommendations...")
        
        # Get ALL tracks as candidates (don't filter upfront)
        # Filtering is too strict with sample catalogue
        # Instead, we'll score all tracks and pick the best ones
        candidates = self.catalogue.tracks
        
        logger.info(f"Evaluating {len(candidates)} tracks from catalogue")
        
        if not candidates:
            logger.warning("No tracks in catalogue")
            return []
        
        # Score each candidate
        scored_tracks = []
        for track in candidates:
            score = self._score_track(track, analysis)
            
            if score > 0.0:  # Only include tracks with some relevance
                scored_tracks.append({
                    'track': track,
                    'score': score
                })
        
        # Sort by score descending
        scored_tracks.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Scored {len(scored_tracks)} tracks")
        
        # Take top N
        top_tracks = scored_tracks[:max_recommendations]
        
        # Convert to TrackRecommendation objects
        recommendations = []
        for item in top_tracks:
            track = item['track']
            score = item['score']
            
            # Create brief explanation (will be enhanced by ExplanationGenerator)
            explanation = self._create_brief_explanation(track, analysis, score)
            
            try:
                recommendation = TrackRecommendation(
                    track_id=track.get('track_id', 'unknown'),
                    track_name=track.get('track_name', 'Unknown Track'),
                    artist=track.get('artist', 'Unknown Artist'),
                    genre_tags=track.get('genre_tags', []),
                    mood_tags=track.get('mood_tags', []),
                    instrument_tags=track.get('instrument_tags', []),
                    relevance_score=score,
                    explanation=explanation,
                    source='Sample Catalogue'
                )
                recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Failed to create recommendation: {e}")
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def _create_brief_explanation(
        self,
        track: Dict[str, Any],
        analysis: MemoryAnalysis,
        score: float
    ) -> str:
        """Create a brief explanation for the recommendation.
        
        Args:
            track: Track metadata
            analysis: Memory analysis
            score: Relevance score
            
        Returns:
            Brief explanation string
        """
        # Find matching elements
        matching_moods = set([m.lower() for m in track.get('mood_tags', [])]).intersection(
            set([e.lower() for e in (analysis.primary_emotions + analysis.secondary_emotions)])
        )
        
        matching_genres = set([g.lower() for g in track.get('genre_tags', [])]).intersection(
            set([g.lower() for g in analysis.genres])
        )
        
        matching_instruments = set([i.lower() for i in track.get('instrument_tags', [])]).intersection(
            set([i.lower() for i in analysis.instruments])
        )
        
        # Build explanation
        parts = []
        
        if matching_moods:
            parts.append(f"captures {', '.join(list(matching_moods)[:2])} emotions")
        
        if matching_genres:
            parts.append(f"{', '.join(list(matching_genres)[:2])} style")
        
        if matching_instruments:
            parts.append(f"features {', '.join(list(matching_instruments)[:2])}")
        
        if parts:
            explanation = f"This track {' with '.join(parts)}, matching your memory's {analysis.atmosphere} atmosphere."
        else:
            explanation = f"This track aligns with the {analysis.atmosphere} atmosphere of your memory."
        
        return explanation

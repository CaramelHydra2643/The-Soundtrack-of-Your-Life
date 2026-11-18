"""
Recommendation Engine

Combines memory analysis, RAG retrieval, and music catalogue to generate recommendations.
"""

import logging
import math
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
        
        # Normalize external CSV/JSON values defensively; pandas may expose
        # missing strings as float NaN values.
        def clean(value: Any) -> str:
            if value is None:
                return ""
            try:
                if isinstance(value, float) and math.isnan(value):
                    return ""
            except (TypeError, ValueError):
                pass
            return str(value).lower().strip()

        search_set = {clean(value) for value in search_tags if clean(value)}
        track_set = {clean(value) for value in track_tags if clean(value)}
        
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
        analysis: MemoryAnalysis,
        retrieved_context: Optional[List[Dict[str, Any]]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Score a track across available signals, renormalizing missing data."""
        all_emotions = analysis.primary_emotions + analysis.secondary_emotions
        track_moods = track.get('mood_tags') or []
        track_genres = track.get('genre_tags') or []
        track_instruments = track.get('instrument_tags') or []
        track_themes = track.get('themes') or []

        preferences = user_preferences or {}
        disliked = {str(value).lower() for value in preferences.get('disliked_genres', [])}
        if disliked.intersection(str(value).lower() for value in track_genres):
            return 0.0
        preferred_genres = preferences.get('preferred_genres', [])
        preferred_languages = preferences.get('preferred_languages', [])
        feedback = preferences.get('feedback', [])
        like_count = sum(1 for item in feedback if item.get('track_id') == track.get('track_id') and item.get('feedback_type') in {'like', 'save'})
        dislike_count = sum(1 for item in feedback if item.get('track_id') == track.get('track_id') and item.get('feedback_type') == 'dislike')
        feedback_signal = min(max(0.5 + (0.2 * like_count) - (0.3 * dislike_count), 0.0), 1.0)
        preference_signal = max(
            self._calculate_tag_overlap(preferred_genres, track_genres),
            self._calculate_tag_overlap(preferred_languages, [track.get('language', '')]),
            feedback_signal if like_count or dislike_count else 0.0,
        )
        scores = {
            'mood': self._calculate_tag_overlap(all_emotions + analysis.themes, track_moods),
            'genre': self._calculate_tag_overlap(analysis.genres, track_genres),
            'language': self._calculate_tag_overlap(
                [getattr(analysis, 'language', '')], [track.get('language', '')]
            ),
            'instrument': self._calculate_tag_overlap(analysis.instruments, track_instruments),
            'theme': self._calculate_tag_overlap(analysis.context + analysis.themes, track_themes + track_genres),
            'audio': self._audio_compatibility(track, analysis),
            'personal': preference_signal,
        }
        weights = {
            'mood': self.settings.weight_mood,
            'genre': self.settings.weight_genre,
            'language': self.settings.weight_language,
            'instrument': self.settings.weight_instrument,
            'theme': self.settings.weight_theme,
            'audio': self.settings.weight_audio,
            'personal': self.settings.weight_personal,
        }

        rag_score = self._rag_signal(track, retrieved_context or [])
        available = {key: value for key, value in scores.items() if key != 'language' or track.get('language')}
        available_weights = {key: weights[key] for key in available if key != 'personal' or scores[key] > 0}
        if rag_score > 0:
            available['rag'] = rag_score
            available_weights['rag'] = 0.10
        available = {key: value for key, value in available.items() if key in available_weights}
        total_weight = sum(available_weights.values())
        final_score = sum(available[key] * available_weights[key] for key in available) / total_weight if total_weight else 0.0
        return min(max(final_score, 0.0), 1.0)

    @staticmethod
    def _audio_compatibility(track: Dict[str, Any], analysis: MemoryAnalysis) -> float:
        """Match qualitative fields and verified numeric audio features."""
        values = []
        energy = track.get('energy')
        if isinstance(energy, (int, float)):
            target = {'very low': 0.15, 'low': 0.30, 'moderate': 0.55, 'high': 0.80}.get(str(analysis.energy).lower())
            if target is not None:
                values.append(max(0.0, 1.0 - abs(float(energy) - target)))
        elif energy:
            values.append(1.0 if str(energy).lower() == str(analysis.energy).lower() else 0.0)

        tempo = track.get('tempo')
        if isinstance(tempo, (int, float)):
            target_tempo = {'slow': 70.0, 'moderate': 110.0, 'fast': 145.0}.get(str(analysis.tempo).lower())
            if target_tempo is not None:
                values.append(max(0.0, 1.0 - abs(float(tempo) - target_tempo) / 120.0))
        elif tempo:
            values.append(1.0 if str(tempo).lower() == str(analysis.tempo).lower() else 0.0)

        valence = track.get('valence')
        emotions = {str(value).lower() for value in analysis.primary_emotions + analysis.secondary_emotions}
        if isinstance(valence, (int, float)) and emotions:
            positive = {'happiness', 'happy', 'gratitude', 'grateful', 'joy', 'excitement', 'hopeful'}
            negative = {'sadness', 'sad', 'grief', 'loneliness', 'anger'}
            target_valence = 0.65 if emotions & positive else 0.35 if emotions & negative else 0.50
            values.append(max(0.0, 1.0 - abs(float(valence) - target_valence)))
        return sum(values) / len(values) if values else 0.0

    def _rag_signal(self, track: Dict[str, Any], retrieved_context: List[Dict[str, Any]]) -> float:
        """Use retrieved topics/text as a small, explainable ranking signal."""
        if not retrieved_context:
            return 0.0
        track_text = ' '.join(str(track.get(field) or '') for field in ('genre_tags', 'mood_tags', 'themes', 'instrument_tags')).lower()
        signals = []
        for document in retrieved_context:
            metadata = document.get('metadata') or {}
            topic = str(metadata.get('topic') or '').lower()
            text = str(document.get('text') or '').lower()
            overlap = self._calculate_tag_overlap(track_text.split(), (topic + ' ' + text).split())
            signals.append(overlap * float(document.get('relevance_score') or 0.0))
        return min(max(max(signals, default=0.0), 0.0), 1.0)

    def generate_recommendations(
        self,
        analysis: MemoryAnalysis,
        retrieved_context: Optional[List[Dict[str, Any]]] = None,
        max_recommendations: Optional[int] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        candidate_tracks: Optional[List[Dict[str, Any]]] = None,
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
        candidates = candidate_tracks if candidate_tracks is not None else self.catalogue.tracks
        
        logger.info(f"Evaluating {len(candidates)} tracks from catalogue")
        
        if not candidates:
            logger.warning("No tracks in catalogue")
            return []
        
        # Score each candidate with the same retrieved context used for ranking.
        scored_tracks = []
        for track in candidates:
            score = self._score_track(track, analysis, retrieved_context, user_preferences)
            if score > 0.0:
                scored_tracks.append({'track': track, 'score': score})

        scored_tracks.sort(key=lambda item: item['score'], reverse=True)
        logger.info(f"Scored {len(scored_tracks)} tracks")

        # MMR-style diversity reranking. Relevance remains primary, while the
        # user's diversity preference controls similarity penalty strength.
        top_tracks = []
        remaining = list(scored_tracks)
        diversity = float((user_preferences or {}).get('diversity', 0.5))
        lambda_relevance = min(max(1.0 - diversity, 0.35), 0.95)

        def similarity(left: Dict[str, Any], right: Dict[str, Any]) -> float:
            left_artist = str(left.get('artist') or '').strip().lower()
            right_artist = str(right.get('artist') or '').strip().lower()
            artist_similarity = 1.0 if left_artist and left_artist == right_artist else 0.0
            left_genres = set(left.get('genre_tags') or [])
            right_genres = set(right.get('genre_tags') or [])
            genre_union = left_genres | right_genres
            genre_similarity = len(left_genres & right_genres) / len(genre_union) if genre_union else 0.0
            return 0.65 * artist_similarity + 0.35 * genre_similarity

        while remaining and len(top_tracks) < max_recommendations:
            best_index = max(
                range(len(remaining)),
                key=lambda index: lambda_relevance * remaining[index]['score']
                - (1.0 - lambda_relevance) * max(
                    (similarity(remaining[index]['track'], selected['track']) for selected in top_tracks),
                    default=0.0,
                ),
            )
            top_tracks.append(remaining.pop(best_index))
        
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
                    source=track.get('source') or 'Local catalogue',
                    preview_url=track.get('preview_url'),
                    listening_url=track.get('listening_url'),
                    album=track.get('album'),
                    language=track.get('language'),
                    artwork_url=track.get('artwork_url'),
                    availability_status=track.get('availability_status') or 'metadata_only'
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

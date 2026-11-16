"""
Music Catalogue Module

Manages music metadata and provides search/filtering capabilities.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd

from config.settings import get_settings

logger = logging.getLogger(__name__)


class MusicCatalogue:
    """Manages music track metadata and search functionality."""

    def __init__(self):
        """Initialize music catalogue."""
        self.settings = get_settings()
        self.catalogue_df: Optional[pd.DataFrame] = None
        self.tracks: List[Dict[str, Any]] = []
        self._load_catalogue()

    def _load_catalogue(self):
        """Load music catalogue from metadata files or create sample data."""
        workspace_root = Path(__file__).parent.parent
        metadata_dir = workspace_root / 'data' / 'music_metadata'
        
        # Try to load from CSV/JSON files
        csv_files = list(metadata_dir.glob('*.csv'))
        json_files = list(metadata_dir.glob('*.json'))
        
        if csv_files:
            logger.info(f"Loading catalogue from {csv_files[0]}")
            try:
                self.catalogue_df = pd.read_csv(csv_files[0])
                self._process_catalogue()
                return
            except Exception as e:
                logger.warning(f"Failed to load CSV: {e}")
        
        if json_files:
            logger.info(f"Loading catalogue from {json_files[0]}")
            try:
                with open(json_files[0], 'r', encoding='utf-8') as f:
                    self.tracks = json.load(f)
                logger.info(f"Loaded {len(self.tracks)} tracks from JSON")
                return
            except Exception as e:
                logger.warning(f"Failed to load JSON: {e}")
        
        # Create sample catalogue
        logger.warning("No catalogue files found, creating sample data")
        self._create_sample_catalogue()

    def _create_sample_catalogue(self):
        """Create a sample music catalogue for demonstration."""
        sample_tracks = [
            {
                'track_id': 'sample_001',
                'track_name': 'Fading Memories',
                'artist': 'Acoustic Dreams',
                'genre_tags': ['indie folk', 'acoustic'],
                'mood_tags': ['nostalgic', 'melancholic', 'reflective'],
                'instrument_tags': ['acoustic guitar', 'piano', 'strings'],
                'tempo': 'moderate',
                'energy': 'low'
            },
            {
                'track_id': 'sample_002',
                'track_name': 'Golden Days',
                'artist': 'The Rememberers',
                'genre_tags': ['indie folk', 'singer-songwriter'],
                'mood_tags': ['nostalgic', 'bittersweet', 'warm'],
                'instrument_tags': ['acoustic guitar', 'harmonica'],
                'tempo': 'slow',
                'energy': 'low'
            },
            {
                'track_id': 'sample_003',
                'track_name': 'Sunrise Celebration',
                'artist': 'Joyful Hearts',
                'genre_tags': ['pop', 'indie pop'],
                'mood_tags': ['happy', 'uplifting', 'energetic'],
                'instrument_tags': ['guitar', 'drums', 'bass'],
                'tempo': 'fast',
                'energy': 'high'
            },
            {
                'track_id': 'sample_004',
                'track_name': 'Quiet Morning',
                'artist': 'Peaceful Sounds',
                'genre_tags': ['ambient', 'new age'],
                'mood_tags': ['peaceful', 'calm', 'serene'],
                'instrument_tags': ['piano', 'synthesizer'],
                'tempo': 'slow',
                'energy': 'very low'
            },
            {
                'track_id': 'sample_005',
                'track_name': 'Last Goodbye',
                'artist': 'Melancholy Strings',
                'genre_tags': ['classical', 'orchestral'],
                'mood_tags': ['sad', 'emotional', 'dramatic'],
                'instrument_tags': ['strings', 'piano', 'cello'],
                'tempo': 'slow',
                'energy': 'low'
            },
            {
                'track_id': 'sample_006',
                'track_name': 'College Nights',
                'artist': 'Youth Revival',
                'genre_tags': ['indie rock', 'alternative'],
                'mood_tags': ['nostalgic', 'energetic', 'youthful'],
                'instrument_tags': ['electric guitar', 'drums', 'bass'],
                'tempo': 'moderate',
                'energy': 'moderate'
            },
            {
                'track_id': 'sample_007',
                'track_name': 'Thankful Heart',
                'artist': 'Grateful Soul',
                'genre_tags': ['folk', 'acoustic pop'],
                'mood_tags': ['grateful', 'warm', 'content'],
                'instrument_tags': ['acoustic guitar', 'piano'],
                'tempo': 'moderate',
                'energy': 'moderate'
            },
            {
                'track_id': 'sample_008',
                'track_name': 'Victory March',
                'artist': 'Triumphant Brass',
                'genre_tags': ['orchestral', 'cinematic'],
                'mood_tags': ['proud', 'triumphant', 'powerful'],
                'instrument_tags': ['brass', 'drums', 'strings'],
                'tempo': 'moderate',
                'energy': 'high'
            },
            {
                'track_id': 'sample_009',
                'track_name': 'Turning Pages',
                'artist': 'Life Stories',
                'genre_tags': ['indie folk', 'singer-songwriter'],
                'mood_tags': ['reflective', 'hopeful', 'bittersweet'],
                'instrument_tags': ['acoustic guitar', 'piano', 'strings'],
                'tempo': 'moderate',
                'energy': 'moderate'
            },
            {
                'track_id': 'sample_010',
                'track_name': 'First Light',
                'artist': 'New Beginnings',
                'genre_tags': ['ambient', 'electronic'],
                'mood_tags': ['hopeful', 'peaceful', 'inspiring'],
                'instrument_tags': ['synthesizer', 'piano'],
                'tempo': 'slow',
                'energy': 'low'
            }
        ]
        
        self.tracks = sample_tracks
        logger.info(f"Created sample catalogue with {len(self.tracks)} tracks")

    def _process_catalogue(self):
        """Process catalogue DataFrame into track dictionaries."""
        if self.catalogue_df is None:
            return
        
        # Convert DataFrame to list of dicts
        # This will depend on actual MTG-Jamendo format
        self.tracks = self.catalogue_df.to_dict('records')
        logger.info(f"Processed {len(self.tracks)} tracks from catalogue")

    def search_tracks(
        self,
        genres: Optional[List[str]] = None,
        moods: Optional[List[str]] = None,
        instruments: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for tracks matching criteria.
        
        Args:
            genres: List of genre tags to match
            moods: List of mood tags to match
            instruments: List of instrument tags to match
            limit: Maximum number of results
            
        Returns:
            List of matching tracks
        """
        if not self.tracks:
            return []
        
        matching_tracks = []
        
        for track in self.tracks:
            match = True
            
            # Check genres
            if genres:
                track_genres = set(track.get('genre_tags', []))
                search_genres = set([g.lower() for g in genres])
                if not track_genres.intersection(search_genres):
                    match = False
            
            # Check moods
            if moods and match:
                track_moods = set([m.lower() for m in track.get('mood_tags', [])])
                search_moods = set([m.lower() for m in moods])
                if not track_moods.intersection(search_moods):
                    match = False
            
            # Check instruments
            if instruments and match:
                track_instruments = set([i.lower() for i in track.get('instrument_tags', [])])
                search_instruments = set([i.lower() for i in instruments])
                if not track_instruments.intersection(search_instruments):
                    match = False
            
            if match:
                matching_tracks.append(track)
            
            if len(matching_tracks) >= limit:
                break
        
        return matching_tracks

    def get_track_by_id(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific track by ID.
        
        Args:
            track_id: Track identifier
            
        Returns:
            Track dict or None
        """
        for track in self.tracks:
            if track.get('track_id') == track_id:
                return track
        return None

    def get_all_tags(self) -> Dict[str, Set[str]]:
        """Get all unique tags in the catalogue.
        
        Returns:
            Dictionary with genre, mood, and instrument tag sets
        """
        genres = set()
        moods = set()
        instruments = set()
        
        for track in self.tracks:
            genres.update(track.get('genre_tags', []))
            moods.update(track.get('mood_tags', []))
            instruments.update(track.get('instrument_tags', []))
        
        return {
            'genres': genres,
            'moods': moods,
            'instruments': instruments
        }

    def get_catalogue_stats(self) -> Dict[str, Any]:
        """Get catalogue statistics.
        
        Returns:
            Dictionary with catalogue statistics
        """
        tags = self.get_all_tags()
        
        return {
            'total_tracks': len(self.tracks),
            'unique_genres': len(tags['genres']),
            'unique_moods': len(tags['moods']),
            'unique_instruments': len(tags['instruments']),
            'sample_tracks': self.tracks[:3] if self.tracks else []
        }

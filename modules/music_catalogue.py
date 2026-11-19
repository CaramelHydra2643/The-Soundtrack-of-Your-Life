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
    """Manages normalized, provenance-aware music metadata."""

    REQUIRED_FIELDS = (
        'track_id', 'track_name', 'artist', 'album', 'release_year', 'language',
        'country', 'region', 'genre_tags', 'subgenre_tags', 'mood_tags', 'themes',
        'instrument_tags', 'energy', 'tempo', 'danceability', 'acousticness',
        'instrumentalness', 'valence', 'arousal', 'artwork_url', 'preview_url',
        'listening_url', 'source', 'license',
        'availability_status', 'musicbrainz_recording_id', 'musicbrainz_artist_id',
        'musicbrainz_release_id', 'musicbrainz_release_group_id', 'musicbrainz_area_id',
        'musicbrainz_match_score'
    )

    def __init__(self):
        """Initialize and load the best available local catalogue."""
        self.settings = get_settings()
        self.catalogue_df: Optional[pd.DataFrame] = None
        self.tracks: List[Dict[str, Any]] = []
        self._load_catalogue()

    @staticmethod
    def _as_tags(value: Any) -> List[str]:
        """Normalize a scalar or delimited tag value to unique lowercase tags."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        values = value if isinstance(value, (list, tuple, set)) else str(value).replace(';', ',').split(',')
        return list(dict.fromkeys(str(item).strip().lower() for item in values if str(item).strip()))

    @classmethod
    def normalize_track(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize common CSV/JSON field names without inventing metadata."""
        def first(*keys: str) -> Any:
            for key in keys:
                value = raw.get(key)
                if value is None or value == "":
                    continue
                if isinstance(value, float) and pd.isna(value):
                    continue
                return value
            return None

        track = {field: None for field in cls.REQUIRED_FIELDS}
        track.update({
            'track_id': str(first('track_id', 'id') or '').strip(),
            'track_name': str(first('track_name', 'name', 'title') or '').strip(),
            'artist': str(first('artist', 'artist_name') or '').strip(),
            'album': first('album', 'album_name'),
            'release_year': first('release_year', 'year'),
            'language': first('language', 'lang'),
            'country': first('country'),
            'region': first('region'),
            'genre_tags': cls._as_tags(first('genre_tags', 'genre', 'genres')),
            'subgenre_tags': cls._as_tags(first('subgenre_tags', 'subgenre')),
            'mood_tags': cls._as_tags(first('mood_tags', 'mood', 'moods')),
            'themes': cls._as_tags(first('themes', 'theme', 'lyrics_themes')),
            'instrument_tags': cls._as_tags(first('instrument_tags', 'instruments', 'instrument')),
            'energy': first('energy'),
            'tempo': first('tempo', 'bpm'),
            'danceability': first('danceability'),
            'acousticness': first('acousticness'),
            'instrumentalness': first('instrumentalness'),
            'valence': first('valence', 'valence_mean'),
            'arousal': first('arousal', 'arousal_mean'),
            'artwork_url': first('artwork_url', 'cover_url'),
            'preview_url': first('preview_url', 'audio_preview'),
            'listening_url': first('listening_url', 'external_url', 'url'),
            'source': first('source') or 'local catalogue',
            'license': first('license', 'licence'),
            'availability_status': first('availability_status') or 'metadata_only',
            'musicbrainz_recording_id': first('musicbrainz_recording_id'),
            'musicbrainz_artist_id': first('musicbrainz_artist_id'),
            'musicbrainz_release_id': first('musicbrainz_release_id'),
            'musicbrainz_release_group_id': first('musicbrainz_release_group_id'),
            'musicbrainz_area_id': first('musicbrainz_area_id'),
            'musicbrainz_match_score': first('musicbrainz_match_score'),
        })
        return track

    @classmethod
    def deduplicate_tracks(cls, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate by stable id, retaining useful fields from later records."""
        by_id: Dict[str, Dict[str, Any]] = {}
        for raw_track in tracks:
            track = cls.normalize_track(raw_track)
            key = track['track_id'] or f"{track['track_name'].lower()}::{track['artist'].lower()}"
            if not key or key == '::':
                continue
            if key not in by_id:
                by_id[key] = track
                continue
            existing = by_id[key]
            if existing.get('source') in (None, '', 'local catalogue') and track.get('source') not in (None, '', 'local catalogue'):
                existing['source'] = track['source']
            for field, value in track.items():
                if value not in (None, '', [], {}) and existing.get(field) in (None, '', [], {}):
                    existing[field] = value
        return list(by_id.values())

    def _load_catalogue(self):
        """Load music catalogue from metadata files or create sample data."""
        workspace_root = Path(__file__).parent.parent
        metadata_dir = workspace_root / 'data' / 'music_metadata'
        
        # Load and merge every local CSV/JSON source. Multiple approved sources
        # (for example MTG-Jamendo and FMA) must not silently replace each other.
        csv_files = sorted(metadata_dir.glob('*.csv'))
        json_files = sorted(metadata_dir.glob('*.json'))
        raw_tracks: List[Dict[str, Any]] = []
        for csv_file in csv_files:
            try:
                logger.info(f"Loading catalogue from {csv_file.name}")
                raw_tracks.extend(pd.read_csv(csv_file).to_dict('records'))
            except Exception as exc:
                logger.warning(f"Failed to load CSV {csv_file}: {exc}")
        for json_file in json_files:
            try:
                logger.info(f"Loading catalogue from {json_file.name}")
                with json_file.open('r', encoding='utf-8') as handle:
                    payload = json.load(handle)
                if isinstance(payload, list):
                    raw_tracks.extend(payload)
                else:
                    logger.warning("Ignoring JSON %s because it is not an array", json_file)
            except Exception as exc:
                logger.warning(f"Failed to load JSON {json_file}: {exc}")
        if raw_tracks:
            self.tracks = self.deduplicate_tracks(raw_tracks)
            logger.info(f"Loaded {len(self.tracks)} normalized tracks from {len(csv_files) + len(json_files)} source files")
            return

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
        
        self.tracks = self.deduplicate_tracks([
            {
                **track,
                'source': 'demo fixture (replace with licensed metadata)',
                'availability_status': 'metadata_only',
            }
            for track in sample_tracks
        ])
        logger.info("No licensed catalogue was found; loaded %d clearly labelled demo fixtures", len(self.tracks))

    def _process_catalogue(self):
        """Process catalogue DataFrame into track dictionaries."""
        if self.catalogue_df is None:
            return
        
        # Normalize common MTG-Jamendo/CSV field names and remove duplicates.
        self.tracks = self.deduplicate_tracks(self.catalogue_df.to_dict('records'))
        logger.info(f"Processed {len(self.tracks)} normalized tracks from catalogue")

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

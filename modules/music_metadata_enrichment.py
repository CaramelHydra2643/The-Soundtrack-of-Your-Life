"""Optional top-track enrichment from official music-service metadata APIs."""

import base64
import hashlib
import json
import logging
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class MusicMetadataEnricher:
    """Enrich selected recommendations without changing catalogue candidates."""

    def __init__(self, cache_dir: Path, spotify_client_id: Optional[str] = None, spotify_client_secret: Optional[str] = None, country: str = "IN") -> None:
        self.cache_dir = Path(cache_dir) / "music_metadata"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.country = country
        self.session = requests.Session()
        self.timeout = 5.0
        self._spotify_token: Optional[str] = None
        self._spotify_token_expires = 0.0

    @staticmethod
    def _normalize(value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    @classmethod
    def _confidence(cls, track: Dict[str, Any], external: Dict[str, Any]) -> float:
        title = SequenceMatcher(None, cls._normalize(track.get("track_name")), cls._normalize(external.get("track_name"))).ratio()
        artist = SequenceMatcher(None, cls._normalize(track.get("artist")), cls._normalize(external.get("artist_name"))).ratio()
        album = SequenceMatcher(None, cls._normalize(track.get("album")), cls._normalize(external.get("album_name"))).ratio() if track.get("album") and external.get("album_name") else 0.5
        return round(0.50 * title + 0.35 * artist + 0.15 * album, 4)

    def _cache_file(self, track: Dict[str, Any]) -> Path:
        key = "::".join(self._normalize(track.get(field)) for field in ("artist", "track_name", "album"))
        return self.cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"

    def _itunes(self, track: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.session.get("https://itunes.apple.com/search", params={"term": f"{track.get('artist', '')} {track.get('track_name', '')}", "country": self.country, "media": "music", "entity": "song", "limit": 5}, timeout=self.timeout)
        response.raise_for_status()
        candidates = response.json().get("results", [])
        best = None
        best_score = 0.0
        for item in candidates:
            external = {"track_name": item.get("trackName"), "artist_name": item.get("artistName"), "album_name": item.get("collectionName")}
            score = self._confidence(track, external)
            if score > best_score:
                best_score, best = score, (item, external)
        if not best or best_score < 0.82:
            return None
        item, external = best
        return {"track_name": external["track_name"], "artist_name": external["artist_name"], "album_name": external["album_name"], "itunes_track_id": item.get("trackId"), "itunes_preview_url": item.get("previewUrl"), "itunes_store_url": item.get("trackViewUrl"), "artwork_url": item.get("artworkUrl100"), "release_year": str(item.get("releaseDate", ""))[:4] or None, "genre": item.get("primaryGenreName"), "confidence": best_score, "metadata_provider": "Apple iTunes"}

    def _spotify_access_token(self) -> Optional[str]:
        if not self.spotify_client_id or not self.spotify_client_secret:
            return None
        if self._spotify_token and time.time() < self._spotify_token_expires:
            return self._spotify_token
        credentials = base64.b64encode(f"{self.spotify_client_id}:{self.spotify_client_secret}".encode()).decode()
        response = self.session.post("https://accounts.spotify.com/api/token", headers={"Authorization": f"Basic {credentials}"}, data={"grant_type": "client_credentials"}, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        self._spotify_token = payload.get("access_token")
        self._spotify_token_expires = time.time() + max(int(payload.get("expires_in", 3600)) - 60, 60)
        return self._spotify_token

    def _spotify(self, track: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        token = self._spotify_access_token()
        if not token:
            return None
        response = self.session.get("https://api.spotify.com/v1/search", headers={"Authorization": f"Bearer {token}"}, params={"q": f"artist:{track.get('artist', '')} track:{track.get('track_name', '')}", "type": "track", "limit": 5}, timeout=self.timeout)
        response.raise_for_status()
        candidates = response.json().get("tracks", {}).get("items", [])
        best = None
        best_score = 0.0
        for item in candidates:
            external = {"track_name": item.get("name"), "artist_name": ((item.get("artists") or [{}])[0]).get("name"), "album_name": (item.get("album") or {}).get("name")}
            score = self._confidence(track, external)
            if score > best_score:
                best_score, best = score, (item, external)
        if not best or best_score < 0.82:
            return None
        item, external = best
        spotify_id = item.get("id")
        return {"spotify_track_id": spotify_id, "spotify_track_url": (item.get("external_urls") or {}).get("spotify"), "spotify_embed_url": f"https://open.spotify.com/embed/track/{spotify_id}" if spotify_id else None, "artwork_url": ((item.get("album") or {}).get("images") or [{}])[0].get("url"), "confidence": best_score, "metadata_provider": "Spotify"}

    def enrich(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich a bounded recommendation list; failures return original tracks."""
        enriched = []
        for track in tracks:
            result = dict(track)
            cache_file = self._cache_file(track)
            try:
                if cache_file.exists():
                    metadata = json.loads(cache_file.read_text(encoding="utf-8"))
                else:
                    metadata = {}
                    try:
                        metadata.update(self._itunes(track) or {})
                    except requests.RequestException as exc:
                        logger.info("iTunes enrichment unavailable: %s", exc)
                    try:
                        metadata.update(self._spotify(track) or {})
                    except requests.RequestException as exc:
                        logger.info("Spotify enrichment unavailable: %s", exc)
                    cache_file.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
                result["metadata_enrichment"] = metadata
            except (OSError, json.JSONDecodeError):
                result["metadata_enrichment"] = {}
            enriched.append(result)
        return enriched

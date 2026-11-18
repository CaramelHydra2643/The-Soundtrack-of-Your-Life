"""Rate-limited, cached MusicBrainz metadata enrichment."""

import hashlib
import json
import logging
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class MusicBrainzEnricher:
    """Enrich track metadata without downloading MusicBrainz database dumps."""

    def __init__(self, cache_dir: Path, user_agent: str = "TheSoundtrackOfYourLife/0.1", min_interval_seconds: float = 1.1, timeout_seconds: float = 15.0, session: Optional[requests.Session] = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.min_interval_seconds = min_interval_seconds
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self._last_request_at = 0.0

    @staticmethod
    def _normalize(value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    def _cache_path(self, track: Dict[str, Any]) -> Path:
        key = "::".join(self._normalize(track.get(field)) for field in ("artist", "track_name", "album"))
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    @classmethod
    def score_candidate(cls, track: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """Score a MusicBrainz recording candidate from 0 to 1."""
        title = cls._normalize(track.get("track_name"))
        artist = cls._normalize(track.get("artist"))
        candidate_title = cls._normalize(candidate.get("title"))
        credits = candidate.get("artist-credit") or []
        candidate_artist = cls._normalize(" ".join(str(item.get("name", "")) for item in credits if isinstance(item, dict)))
        title_score = SequenceMatcher(None, title, candidate_title).ratio() if title else 0.0
        artist_score = SequenceMatcher(None, artist, candidate_artist).ratio() if artist else 0.0
        return 0.65 * title_score + 0.35 * artist_score

    def _wait_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)

    def _search(self, track: Dict[str, Any]) -> Dict[str, Any]:
        query_parts = []
        if track.get("track_name"):
            query_parts.append(f'track:"{track["track_name"]}"')
        if track.get("artist"):
            query_parts.append(f'artist:"{track["artist"]}"')
        if track.get("album"):
            query_parts.append(f'release:"{track["album"]}"')
        if not query_parts:
            return {"recordings": []}
        self._wait_for_rate_limit()
        response = self.session.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": " AND ".join(query_parts), "fmt": "json", "limit": 5},
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            timeout=self.timeout_seconds,
        )
        self._last_request_at = time.monotonic()
        response.raise_for_status()
        return response.json()

    def enrich_track(self, track: Dict[str, Any], min_score: float = 0.80) -> Dict[str, Any]:
        """Return an enriched copy; uncertain matches remain explicitly unlinked."""
        enriched = dict(track)
        enriched.update({
            "musicbrainz_recording_id": None,
            "musicbrainz_artist_id": None,
            "musicbrainz_release_id": None,
            "musicbrainz_release_group_id": None,
            "musicbrainz_match_score": None,
        })
        cache_path = self._cache_path(track)
        try:
            if cache_path.exists():
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                payload = self._search(track)
                cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            candidates = payload.get("recordings", [])
            best = max(candidates, key=lambda item: self.score_candidate(track, item), default=None)
            if not best:
                return enriched
            score = self.score_candidate(track, best)
            if score < min_score:
                return enriched
            enriched["musicbrainz_recording_id"] = best.get("id")
            credits = best.get("artist-credit") or []
            if credits and isinstance(credits[0], dict):
                enriched["musicbrainz_artist_id"] = (credits[0].get("artist") or {}).get("id")
            releases = best.get("releases") or []
            if releases:
                release = releases[0]
                enriched["musicbrainz_release_id"] = release.get("id")
                enriched["album"] = enriched.get("album") or release.get("title")
                enriched["country"] = enriched.get("country") or release.get("country")
                enriched["release_year"] = enriched.get("release_year") or str(release.get("date", ""))[:4] or None
                enriched["musicbrainz_release_group_id"] = (release.get("release-group") or {}).get("id")
            enriched["musicbrainz_match_score"] = round(score, 4)
        except (requests.RequestException, OSError, json.JSONDecodeError) as exc:
            logger.warning("MusicBrainz enrichment failed for %s: %s", track.get("track_id"), exc)
        return enriched

"""SQLite-backed index for normalized music catalogue metadata."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from config.settings import get_settings


class CatalogueStore:
    """Persist searchable catalogue metadata separately from MemoryVault."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (get_settings().data_dir / "catalogue.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS tracks (
                    track_id TEXT PRIMARY KEY,
                    track_name TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT,
                    language TEXT,
                    country TEXT,
                    region TEXT,
                    release_year INTEGER,
                    source TEXT NOT NULL,
                    license TEXT,
                    availability_status TEXT NOT NULL,
                    genre_tags TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tracks_language ON tracks(language);
                CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
                CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source);
                CREATE INDEX IF NOT EXISTS idx_tracks_availability ON tracks(availability_status);
                CREATE INDEX IF NOT EXISTS idx_tracks_release_year ON tracks(release_year);
            """)

    def replace_batch(self, tracks: Iterable[Dict[str, Any]], batch_size: int = 1000) -> int:
        """Upsert normalized tracks in bounded transactions."""
        batch = []
        total = 0
        with self._connect() as connection:
            for track in tracks:
                track_id = str(track.get("track_id") or "").strip()
                if not track_id or not track.get("track_name") or not track.get("artist"):
                    continue
                batch.append((
                    track_id, str(track["track_name"]), str(track["artist"]), track.get("album"),
                    track.get("language"), track.get("country"), track.get("region"),
                    track.get("release_year"), str(track.get("source") or ""), track.get("license"),
                    str(track.get("availability_status") or "metadata_only"),
                    json.dumps(track.get("genre_tags") or [], ensure_ascii=False),
                    json.dumps(track, ensure_ascii=False),
                ))
                if len(batch) >= batch_size:
                    self._upsert(connection, batch)
                    total += len(batch)
                    batch.clear()
            if batch:
                self._upsert(connection, batch)
                total += len(batch)
        return total

    @staticmethod
    def _upsert(connection: sqlite3.Connection, batch: List[tuple]) -> None:
        connection.executemany("""
            INSERT INTO tracks
            (track_id, track_name, artist, album, language, country, region,
             release_year, source, license, availability_status, genre_tags, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(track_id) DO UPDATE SET
              track_name=excluded.track_name, artist=excluded.artist, album=excluded.album,
              language=excluded.language, country=excluded.country, region=excluded.region,
              release_year=excluded.release_year, source=excluded.source, license=excluded.license,
              availability_status=excluded.availability_status, genre_tags=excluded.genre_tags,
              metadata_json=excluded.metadata_json
        """, batch)

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM tracks").fetchone()[0])

    def search_ids(self, language: Optional[str] = None, genre: Optional[str] = None, region: Optional[str] = None, limit: int = 1000) -> List[str]:
        """Return candidate IDs using indexed metadata filters."""
        clauses = []
        params: List[Any] = []
        if language:
            clauses.append("lower(language) = lower(?)")
            params.append(language)
        if region:
            clauses.append("lower(region) = lower(?)")
            params.append(region)
        if genre:
            clauses.append("lower(genre_tags) LIKE ?")
            params.append(f"%{genre.lower()}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(f"SELECT track_id FROM tracks {where} LIMIT ?", (*params, limit)).fetchall()
        return [str(row["track_id"]) for row in rows]

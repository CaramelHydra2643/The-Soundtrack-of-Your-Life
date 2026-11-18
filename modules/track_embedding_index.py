"""Persistent semantic index for real catalogue tracks."""

from typing import Any, Dict, Iterable, List

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config.settings import get_settings


class TrackEmbeddingIndex:
    """Build/query a separate Chroma collection for track-level retrieval."""

    def __init__(self, model: SentenceTransformer | None = None) -> None:
        settings = get_settings()
        self.settings = settings
        self.model = model
        self.client = chromadb.PersistentClient(
            path=str(settings.vector_db_dir),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.client.get_or_create_collection(
            name="music_tracks",
            metadata={"description": "Semantic index of normalized music tracks", "hnsw:space": "cosine"},
        )

    @staticmethod
    def profile_text(track: Dict[str, Any]) -> str:
        """Create a stable, metadata-only track profile for embedding."""
        fields = (
            track.get("track_name"), track.get("artist"), track.get("album"),
            track.get("language"), track.get("country"), track.get("region"),
            track.get("genre_tags"), track.get("subgenre_tags"), track.get("mood_tags"),
            track.get("themes"), track.get("instrument_tags"), track.get("energy"),
            track.get("tempo"), track.get("license"),
        )
        return " | ".join(str(value) for value in fields if value not in (None, "", []))

    def _get_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(self.settings.embedding_model, device=self.settings.embedding_device)
        return self.model

    @staticmethod
    def normalize_distance(distance: float, metric: str) -> float:
        """Convert Chroma cosine/L2 distances into a bounded relevance score."""
        value = max(float(distance), 0.0)
        if metric in {"cosine", "cosine_distance"}:
            return min(max(1.0 - value, 0.0), 1.0)
        return min(max(1.0 / (1.0 + value), 0.0), 1.0)

    def _collection_metric(self) -> str:
        metadata = getattr(self.collection, "metadata", {}) or {}
        return str(metadata.get("hnsw:space", "cosine")).lower()

    def build(self, tracks: Iterable[Dict[str, Any]], batch_size: int = 128, reset: bool = False) -> int:
        """Embed metadata in batches; no audio is downloaded or embedded."""
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if reset:
            try:
                self.client.delete_collection("music_tracks")
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name="music_tracks",
                metadata={"description": "Semantic index of normalized music tracks", "hnsw:space": "cosine"},
            )
        records = []
        seen_ids = set()
        for track in tracks:
            track_id = str(track.get("track_id") or "").strip()
            if not track_id or track_id in seen_ids:
                continue
            seen_ids.add(track_id)
            records.append(track)
        model = self._get_model()
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            profiles = [self.profile_text(track) for track in batch]
            self.collection.upsert(
                ids=[str(track["track_id"]) for track in batch],
                documents=profiles,
                metadatas=[{
                    "track_id": str(track["track_id"]),
                    "source": str(track.get("source") or ""),
                    "license": str(track.get("license") or ""),
                } for track in batch],
                embeddings=model.encode(profiles, normalize_embeddings=True).tolist(),
            )
        return self.collection.count()

    def is_ready(self) -> bool:
        return self.collection.count() > 0

    def query(self, text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return matching track IDs and normalized cosine relevance."""
        if not text.strip() or not self.is_ready():
            return []
        results = self.collection.query(
            query_embeddings=[self._get_model().encode(text, normalize_embeddings=True).tolist()],
            n_results=limit,
            include=["metadatas", "distances", "documents"],
        )
        return [
            {
                "track_id": results["ids"][0][index],
                "distance": results["distances"][0][index],
                "relevance_score": self.normalize_distance(
                    results["distances"][0][index], self._collection_metric()
                ),
                "metadata": results["metadatas"][0][index],
            }
            for index in range(len(results["ids"][0]))
        ]

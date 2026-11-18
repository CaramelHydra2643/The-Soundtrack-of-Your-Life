"""Import the FMA metadata archive into the normalized local catalogue.

This adapter imports metadata/features only. It does not download FMA audio.
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.music_catalogue import MusicCatalogue


def parse_list(value: Any) -> list[Any]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else [parsed]
    except (ValueError, SyntaxError):
        return [value]


def flatten_column(column: tuple[Any, ...]) -> tuple[str, str]:
    """Return FMA's top-level group and semantic second-level field."""
    return str(column[0]), str(column[1])


def import_fma(dataset_root: Path, output: Path) -> dict[str, int]:
    metadata_path = dataset_root / "data" / "fma_metadata" / "tracks.csv"
    genres_path = dataset_root / "data" / "fma_metadata" / "genres.csv"
    if not metadata_path.exists():
        raise FileNotFoundError("Expected data/fma_metadata/tracks.csv in the FMA clone.")

    genre_names: dict[str, str] = {}
    if genres_path.exists():
        genres = pd.read_csv(genres_path)
        genre_names = dict(zip(genres["genre_id"].astype(str), genres["title"].astype(str)))

    frame = pd.read_csv(metadata_path, header=[0, 1, 2], index_col=0)
    records: list[dict[str, Any]] = []
    for track_id, row in frame.iterrows():
        values: dict[tuple[str, str], Any] = {}
        for column, value in row.items():
            parent, leaf = flatten_column(column)
            values[(parent, leaf)] = value

        genre_ids = [str(value) for value in parse_list(values.get(("track", "genres_all")))]
        genre_tags = [genre_names[value].lower() for value in genre_ids if value in genre_names]
        top_genre = values.get(("track", "genre_top"))
        if top_genre and not (isinstance(top_genre, float) and pd.isna(top_genre)):
            genre_tags.append(str(top_genre).lower())

        raw = {
            "track_id": f"fma_{int(track_id):06d}",
            "track_name": values.get(("track", "title")),
            "artist": values.get(("artist", "name")),
            "album": values.get(("album", "title")),
            "release_year": None,
            "language": values.get(("track", "language_code")),
            "genre_tags": list(dict.fromkeys(genre_tags)),
            "mood_tags": [],
            "themes": [],
            "instrument_tags": [],
            "tempo": None,
            "energy": None,
            "artwork_url": None,
            "preview_url": None,
            "listening_url": None,
            "source": "Free Music Archive",
            "license": values.get(("track", "license")),
            "availability_status": "metadata_only",
        }
        track = MusicCatalogue.normalize_track(raw)
        if track["track_id"] and track["track_name"] and track["artist"]:
            records.append(track)

    normalized = MusicCatalogue.deduplicate_tracks(records)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(normalized, ensure_ascii=False), encoding="utf-8")
    return {"metadata_rows": len(records), "unique_tracks": len(normalized)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/music_metadata/fma_catalogue.json"))
    args = parser.parse_args()
    print(json.dumps(import_fma(args.dataset_root, args.output), indent=2))
    print(f"Wrote normalized catalogue to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

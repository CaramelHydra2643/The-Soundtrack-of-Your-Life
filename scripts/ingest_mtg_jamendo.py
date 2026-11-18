"""Import MTG-Jamendo metadata and tags from an existing dataset clone.

This adapter consumes TSV metadata/tag files only; it does not download audio.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.music_catalogue import MusicCatalogue


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def import_catalogue(dataset_root: Path, output: Path) -> dict[str, int]:
    metadata_path = dataset_root / "data" / "raw.meta.tsv"
    tag_path = dataset_root / "data" / "raw_30s_cleantags_50artists.tsv"
    if not metadata_path.exists() or not tag_path.exists():
        raise FileNotFoundError("Dataset must contain data/raw.meta.tsv and data/raw_30s_cleantags_50artists.tsv")

    tags = defaultdict(lambda: defaultdict(list))
    for row in rows(tag_path):
        for raw_tag in (row.get("TAGS") or "").split(","):
            category, separator, value = raw_tag.partition("---")
            if separator and value:
                tags[row.get("TRACK_ID", "")][category].append(value)

    records: list[dict[str, Any]] = []
    for row in rows(metadata_path):
        track_id = row.get("TRACK_ID", "")
        grouped = tags.get(track_id, {})
        raw = {
            "track_id": track_id,
            "track_name": row.get("TRACK_NAME"),
            "artist": row.get("ARTIST_NAME"),
            "album": row.get("ALBUM_NAME"),
            "release_year": (row.get("RELEASEDATE") or "")[:4] or None,
            "genre_tags": grouped.get("genre", []),
            "instrument_tags": grouped.get("instrument", []),
            "mood_tags": grouped.get("mood/theme", []),
            "listening_url": row.get("URL"),
            "source": "MTG-Jamendo",
            "license": "See dataset audio_licenses.txt",
            "availability_status": "external_listening",
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
    parser.add_argument("--output", type=Path, default=Path("data/music_metadata/mtg_jamendo_catalogue.json"))
    args = parser.parse_args()
    summary = import_catalogue(args.dataset_root, args.output)
    print(json.dumps(summary, indent=2))
    print(f"Wrote normalized catalogue to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Normalize DEAM song-level valence/arousal annotations for calibration.

The DEAM audio/features remain local data assets; this script writes a compact
JSON summary for future emotion-to-music calibration and does not copy audio.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_annotation_file(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def ingest(root: Path, output: Path) -> dict[str, int]:
    song_level = root / "annotations" / "annotations averaged per song" / "song_level"
    files = sorted(song_level.glob("static_annotations_averaged_songs_*.csv"))
    if not files:
        raise FileNotFoundError("No averaged DEAM song-level annotation CSV files were found.")
    records: dict[str, dict[str, Any]] = {}
    for path in files:
        for row in read_annotation_file(path):
            song_id = str(row.get("song_id", "")).strip()
            if not song_id:
                continue
            records[song_id] = {
                "song_id": int(song_id),
                "valence_mean": float(row[" valence_mean"]),
                "valence_std": float(row[" valence_std"]),
                "arousal_mean": float(row[" arousal_mean"]),
                "arousal_std": float(row[" arousal_std"]),
                "source": "DEAM",
            }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(list(records.values()), ensure_ascii=False), encoding="utf-8")
    return {"annotation_files": len(files), "songs": len(records)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Extracted DEAM annotations directory")
    parser.add_argument("--output", type=Path, default=Path("data/emotion_annotations/deam_song_emotions.json"))
    args = parser.parse_args()
    print(json.dumps(ingest(args.root, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Extract compact FMA Echo Nest audio features into catalogue sidecar JSON."""

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def clean(value: Any) -> Any:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value) if isinstance(value, (int, float)) else value


def import_features(path: Path, output: Path) -> dict[str, int]:
    frame = pd.read_csv(path, header=[0, 1, 2], index_col=0)
    selected = {
        "acousticness": ("echonest", "audio_features", "acousticness"),
        "danceability": ("echonest", "audio_features", "danceability"),
        "energy": ("echonest", "audio_features", "energy"),
        "instrumentalness": ("echonest", "audio_features", "instrumentalness"),
        "tempo": ("echonest", "audio_features", "tempo"),
        "valence": ("echonest", "audio_features", "valence"),
    }
    records = []
    for track_id, row in frame.iterrows():
        record = {"track_id": f"fma_{int(track_id):06d}", "source": "Free Music Archive", "feature_source": "FMA Echo Nest"}
        for name, column in selected.items():
            record[name] = clean(row.get(column))
        if any(record[name] is not None for name in selected):
            records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return {"rows": len(frame), "feature_records": len(records)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features_csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/music_metadata/fma_audio_features.json"))
    args = parser.parse_args()
    print(json.dumps(import_features(args.features_csv, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

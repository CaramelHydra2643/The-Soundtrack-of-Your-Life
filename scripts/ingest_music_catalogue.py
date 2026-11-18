"""Ingest approved CSV/JSON music metadata into the normalized local catalogue.

This script intentionally does not scrape services or download audio. It preserves
source/licence fields and accepts only user-provided metadata files.
"""

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.music_catalogue import MusicCatalogue

logger = logging.getLogger(__name__)


def read_records(input_path: Path) -> Iterable[Dict[str, Any]]:
    """Read records from a UTF-8 CSV or JSON array/object file."""
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)
        return
    if suffix == ".json":
        with input_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        records = payload if isinstance(payload, list) else payload.get("tracks", [])
        if not isinstance(records, list):
            raise ValueError("JSON input must be an array or an object containing a 'tracks' array.")
        yield from records
        return
    raise ValueError("Input must be a .csv or .json file.")


def is_http_url(value: Any) -> bool:
    """Accept only normal HTTP(S) URLs for external metadata links."""
    if not value:
        return True
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_records(
    records: Iterable[Dict[str, Any]],
    source_override: str | None = None,
    license_override: str | None = None,
    availability_override: str | None = None,
) -> tuple[List[Dict[str, Any]], List[str]]:
    """Normalize records and return valid records plus diagnostics."""
    valid: List[Dict[str, Any]] = []
    diagnostics: List[str] = []
    for row_number, raw in enumerate(records, start=2):
        if not isinstance(raw, dict):
            diagnostics.append(f"row {row_number}: ignored non-object record")
            continue
        track = MusicCatalogue.normalize_track(raw)
        if source_override:
            track["source"] = source_override
        if license_override and not track.get("license"):
            track["license"] = license_override
        if availability_override:
            track["availability_status"] = availability_override
        missing = [field for field in ("track_id", "track_name", "artist") if not track.get(field)]
        invalid_urls = [
            field for field in ("artwork_url", "preview_url", "listening_url")
            if not is_http_url(track.get(field))
        ]
        if missing:
            diagnostics.append(f"row {row_number}: missing {', '.join(missing)}")
            continue
        if invalid_urls:
            diagnostics.append(f"row {row_number}: cleared invalid URL fields {', '.join(invalid_urls)}")
            for field in invalid_urls:
                track[field] = None
        valid.append(track)
    return MusicCatalogue.deduplicate_tracks(valid), diagnostics


def ingest(
    input_path: Path,
    output_path: Path,
    source_override: str | None = None,
    license_override: str | None = None,
    availability_override: str | None = None,
) -> Dict[str, Any]:
    """Ingest and write normalized records, returning a diagnostic summary."""
    records, diagnostics = normalize_records(
        read_records(input_path), source_override, license_override, availability_override
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {
        "input": str(input_path),
        "output": str(output_path),
        "records_written": len(records),
        "diagnostics": diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Approved CSV or JSON metadata file")
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/music_metadata/catalogue.json"),
        help="Normalized JSON output path",
    )
    parser.add_argument("--source", help="Source name applied when source is missing")
    parser.add_argument("--license", dest="license_name", help="Licence applied when licence is missing")
    parser.add_argument("--availability-status", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    try:
        summary = ingest(args.input, args.output, args.source, args.license_name, args.availability_status)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Catalogue ingestion failed: %s", exc)
        return 1
    logger.info("Wrote %d normalized tracks to %s", summary["records_written"], summary["output"])
    for diagnostic in summary["diagnostics"]:
        logger.warning(diagnostic)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

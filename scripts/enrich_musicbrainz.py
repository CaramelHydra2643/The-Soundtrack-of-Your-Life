"""Enrich a bounded batch of local catalogue records from MusicBrainz.

The script is deliberately bounded and rate-limited. It uses the read API and
caches raw responses; it does not download MusicBrainz database dumps.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.musicbrainz_enricher import MusicBrainzEnricher


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Normalized catalogue JSON")
    parser.add_argument("--output", type=Path, default=Path("data/music_metadata/musicbrainz_enriched.json"))
    parser.add_argument("--cache", type=Path, default=Path("data/cache/musicbrainz"))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-score", type=float, default=0.80)
    parser.add_argument("--user-agent", default="TheSoundtrackOfYourLife/0.1")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 5000:
        raise SystemExit("--limit must be between 1 and 5000")
    records = json.loads(args.input.read_text(encoding="utf-8"))
    enricher = MusicBrainzEnricher(args.cache, user_agent=args.user_agent)
    batch = records[args.offset:args.offset + args.limit]
    enriched = [enricher.enrich_track(track, min_score=args.min_score) for track in batch]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False), encoding="utf-8")
    matched = sum(1 for track in enriched if track.get("musicbrainz_recording_id"))
    print(json.dumps({"processed": len(enriched), "matched": matched, "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

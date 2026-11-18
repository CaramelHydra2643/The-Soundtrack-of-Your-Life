"""Build the separate music_tracks ChromaDB index from local metadata."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.music_catalogue import MusicCatalogue
from modules.track_embedding_index import TrackEmbeddingIndex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000, help="Number of tracks to index; use 0 for all remaining tracks")
    parser.add_argument("--offset", type=int, default=0, help="Number of catalogue records to skip for resumable builds")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.limit < 0 or args.offset < 0 or args.batch_size < 1:
        raise SystemExit("--limit and --offset must be non-negative; --batch-size must be positive")
    catalogue = MusicCatalogue()
    tracks = catalogue.tracks[args.offset:] if args.limit == 0 else catalogue.tracks[args.offset:args.offset + args.limit]
    count = TrackEmbeddingIndex().build(tracks, batch_size=args.batch_size, reset=args.reset)
    print(f"Indexed {len(tracks)} track profiles from offset {args.offset}; collection now contains {count} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Print verified catalogue coverage and metadata diagnostics."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.music_catalogue import MusicCatalogue


if __name__ == "__main__":
    tracks = MusicCatalogue().tracks
    source = Counter(str(track.get("source") or "unknown") for track in tracks)
    languages = Counter(str(track.get("language") or "unknown") for track in tracks)
    summary = {
        "total_tracks": len(tracks),
        "tracks_per_source": dict(source),
        "top_languages": dict(languages.most_common(20)),
        "missing_artist": sum(not track.get("artist") for track in tracks),
        "missing_title": sum(not track.get("track_name") for track in tracks),
        "missing_language": sum(not track.get("language") for track in tracks),
        "missing_license": sum(not track.get("license") for track in tracks),
        "with_artwork": sum(bool(track.get("artwork_url")) for track in tracks),
        "with_preview": sum(bool(track.get("preview_url")) for track in tracks),
        "with_listening_url": sum(bool(track.get("listening_url")) for track in tracks),
        "metadata_only": sum(track.get("availability_status") == "metadata_only" for track in tracks),
        "with_numeric_audio": sum(any(track.get(field) is not None for field in ("energy", "tempo", "valence", "danceability", "acousticness")) for track in tracks),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

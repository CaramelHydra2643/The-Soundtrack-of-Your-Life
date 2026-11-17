from modules.music_catalogue import MusicCatalogue


def test_normalize_track_preserves_nullable_provenance_fields():
    track = MusicCatalogue.normalize_track({
        "id": "jamendo-1", "name": "River Home", "artist_name": "Open Roads",
        "genre": "Folk", "language": "English", "source": "MTG-Jamendo",
        "license": "CC BY-NC-SA",
    })
    assert track["track_id"] == "jamendo-1"
    assert track["track_name"] == "River Home"
    assert track["artist"] == "Open Roads"
    assert track["genre_tags"] == ["folk"]
    assert track["preview_url"] is None
    assert track["source"] == "MTG-Jamendo"
    assert track["license"] == "CC BY-NC-SA"


def test_deduplicate_tracks_prefers_first_complete_record():
    tracks = [
        {"track_id": "x", "track_name": "Song", "artist": "Artist", "genre_tags": []},
        {"track_id": "x", "track_name": "Song", "artist": "Artist", "genre_tags": ["folk"]},
    ]
    deduped = MusicCatalogue.deduplicate_tracks(tracks)
    assert len(deduped) == 1
    assert deduped[0]["genre_tags"] == ["folk"]

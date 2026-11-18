from pathlib import Path

from modules.musicbrainz_enricher import MusicBrainzEnricher


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse(self.payload)


def test_musicbrainz_matching_and_cache(tmp_path):
    session = FakeSession({
        "recordings": [{
            "id": "recording-1",
            "title": "Open Sky",
            "artist-credit": [{"name": "Artist One", "artist": {"id": "artist-1"}}],
            "releases": [{"id": "release-1", "title": "Blue Album", "date": "2020-01-01", "country": "GB", "release-group": {"id": "group-1"}}],
        }]
    })
    enricher = MusicBrainzEnricher(Path(tmp_path), min_interval_seconds=0, session=session)
    track = {"track_id": "x", "track_name": "Open Sky", "artist": "Artist One", "album": "Blue Album"}
    first = enricher.enrich_track(track)
    second = enricher.enrich_track(track)
    assert first["musicbrainz_recording_id"] == "recording-1"
    assert first["country"] == "GB"
    assert second["musicbrainz_release_id"] == "release-1"
    assert session.calls == 1


def test_musicbrainz_rejects_low_confidence_match(tmp_path):
    session = FakeSession({"recordings": [{"id": "wrong", "title": "Different", "artist-credit": [{"name": "Other"}]}]})
    enricher = MusicBrainzEnricher(Path(tmp_path), min_interval_seconds=0, session=session)
    result = enricher.enrich_track({"track_id": "x", "track_name": "Open Sky", "artist": "Artist One"}, min_score=0.9)
    assert result["musicbrainz_recording_id"] is None

from pathlib import Path

import requests

from modules.music_metadata_enrichment import MusicMetadataEnricher


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload=None, error=False):
        self.payload = payload or {"results": []}
        self.error = error

    def get(self, *args, **kwargs):
        if self.error:
            raise requests.Timeout("offline")
        return FakeResponse(self.payload)


def test_itunes_match_attaches_artwork_preview_and_store_link(tmp_path):
    session = FakeSession({"results": [{
        "trackName": "Open Sky", "artistName": "Artist One", "collectionName": "Blue Album",
        "trackId": 42, "previewUrl": "https://example.test/preview.m4a",
        "trackViewUrl": "https://music.apple.com/test", "artworkUrl100": "https://example.test/art.jpg",
    }]})
    enricher = MusicMetadataEnricher(Path(tmp_path))
    enricher.session = session
    result = enricher.enrich([{"track_id": "x", "track_name": "Open Sky", "artist": "Artist One", "album": "Blue Album"}])
    metadata = result[0]["metadata_enrichment"]
    assert metadata["itunes_track_id"] == 42
    assert metadata["itunes_preview_url"]
    assert metadata["artwork_url"]


def test_weak_external_match_is_rejected(tmp_path):
    session = FakeSession({"results": [{"trackName": "Different", "artistName": "Other"}]})
    enricher = MusicMetadataEnricher(Path(tmp_path))
    enricher.session = session
    result = enricher.enrich([{"track_id": "x", "track_name": "Open Sky", "artist": "Artist One"}])
    assert result[0]["metadata_enrichment"] == {}


def test_external_outage_keeps_original_track(tmp_path):
    enricher = MusicMetadataEnricher(Path(tmp_path))
    enricher.session = FakeSession(error=True)
    track = {"track_id": "x", "track_name": "Open Sky", "artist": "Artist One"}
    result = enricher.enrich([track])
    assert result[0]["track_id"] == "x"
    assert result[0]["metadata_enrichment"] == {}

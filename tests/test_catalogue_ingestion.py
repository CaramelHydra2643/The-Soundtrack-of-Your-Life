import json

from scripts.ingest_mtg_jamendo import import_catalogue


def test_mtg_ingestion_preserves_metadata_and_tags(tmp_path):
    root = tmp_path / "mtg"
    data = root / "data"
    data.mkdir(parents=True)
    (data / "raw.meta.tsv").write_text(
        "TRACK_ID\tTRACK_NAME\tARTIST_NAME\tALBUM_NAME\tRELEASEDATE\tURL\n"
        "track_1\tOpen Sky\tArtist One\tAlbum\t2020-01-01\thttps://jamendo.com/track/1\n",
        encoding="utf-8",
    )
    (data / "raw_30s_cleantags_50artists.tsv").write_text(
        "TRACK_ID\tARTIST_ID\tALBUM_ID\tPATH\tDURATION\tTAGS\n"
        "track_1\ta\tb\t1/1.mp3\t30\tgenre---folk,instrument---piano,mood/theme---peaceful\n",
        encoding="utf-8",
    )
    output = tmp_path / "catalogue.json"
    summary = import_catalogue(root, output)
    records = json.loads(output.read_text(encoding="utf-8"))
    assert summary == {"metadata_rows": 1, "unique_tracks": 1}
    assert records[0]["genre_tags"] == ["folk"]
    assert records[0]["mood_tags"] == ["peaceful"]
    assert records[0]["license"] == "See dataset audio_licenses.txt"

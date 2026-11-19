"""Build the SQLite catalogue metadata index from local normalized JSON/CSV sources."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.catalogue_store import CatalogueStore
from modules.music_catalogue import MusicCatalogue


if __name__ == "__main__":
    catalogue = MusicCatalogue()
    store = CatalogueStore()
    imported = store.replace_batch(catalogue.tracks)
    print({"imported": imported, "stored": store.count(), "sources": sorted({track.get("source") for track in catalogue.tracks})})

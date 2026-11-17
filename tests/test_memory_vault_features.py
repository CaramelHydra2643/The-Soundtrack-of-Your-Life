from modules.memory_vault import MemoryVault


def vault(tmp_path):
    instance = object.__new__(MemoryVault)
    instance.db_path = tmp_path / "memories.db"
    instance._initialize_database()
    return instance


def test_feedback_preferences_export_and_delete_all(tmp_path):
    store = vault(tmp_path)
    assert store.record_feedback("track-1", "like") is True
    assert store.record_feedback("track-1", "invalid") is False
    assert store.save_preferences({"preferred_genres": ["folk"], "diversity": 0.8}) is True
    assert store.get_preferences()["preferred_genres"] == ["folk"]
    exported = store.export_data()
    assert exported["feedback"][0]["feedback_type"] == "like"
    assert exported["preferences"]["diversity"] == 0.8
    assert store.delete_all_data() is True
    assert store.get_feedback() == []
    assert store.get_preferences()["preferred_genres"] == []

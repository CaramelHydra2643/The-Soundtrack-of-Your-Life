"""Opt-in Ollama integration test.

Run explicitly with: pytest -m integration tests/test_ollama.py
It is skipped by default because it requires a running local Ollama model.
"""

import os
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_LOCAL_INTEGRATION") != "1",
    reason="Set RUN_LOCAL_INTEGRATION=1 to run local Ollama integration tests",
)
def test_local_ollama_memory_analysis():
    from modules.memory_analyzer import MemoryAnalyzer

    memory = "My friends and I said goodbye after college, feeling happy and nostalgic."
    analysis = MemoryAnalyzer().analyze_memory(memory)
    assert analysis is not None
    assert analysis.primary_emotions

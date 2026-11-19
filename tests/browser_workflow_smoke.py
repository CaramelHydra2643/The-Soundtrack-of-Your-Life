import json
from playwright.sync_api import sync_playwright


SOUNDTRACK = {
    "memory_analysis": {
        "memory_title": "Summer Family Memory",
        "summary": "A meaningful family memory with warmth and nostalgia.",
        "primary_emotions": ["nostalgia"], "secondary_emotions": ["warmth"],
        "emotional_intensity": 7, "themes": ["family", "childhood"], "context": ["home"],
        "genres": ["folk"], "instruments": ["piano"], "tempo": "moderate", "energy": "low",
        "atmosphere": "warm and reflective", "musical_description": "Warm reflective music for a meaningful family memory.",
        "language": "English", "requested_music_language": None, "cultural_context": [],
    },
    "recommendations": [{
        "track_id": "smoke_1", "track_name": "Open Sky", "artist": "Test Artist", "album": "Test Album",
        "language": "English", "genre_tags": ["folk"], "mood_tags": ["warm"], "instrument_tags": ["piano"],
        "relevance_score": 0.84, "explanation": "This track matches the warm reflective memory.",
        "source": "test", "availability_status": "metadata_only",
    }],
    "overall_explanation": "This soundtrack reflects the warm and nostalgic character of your family memory.",
    "retrieved_knowledge_summary": [],
}

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    saved = {"value": False}

    def route_handler(route):
        request = route.request
        if request.method == "POST" and request.url.endswith("/api/soundtracks"):
            route.fulfill(status=200, content_type="application/json", body=json.dumps(SOUNDTRACK))
        elif request.method == "POST" and request.url.endswith("/api/memories"):
            saved["value"] = True
            route.fulfill(status=200, content_type="application/json", body='{"memory_id": 42}')
        elif request.method == "GET" and "/api/memories" in request.url:
            memories = [{"id": 42, "memory_title": "Summer Family Memory", "summary": "A meaningful family memory with warmth and nostalgia.", "story": "My family memory", "emotions": ["nostalgia"], "themes": ["family"], "recommendations": [{"track_name": "Open Sky", "artist": "Test Artist"}], "created_at": "2026-11-19T00:00:00Z"}]
            route.fulfill(status=200, content_type="application/json", body=json.dumps(memories))
        else:
            route.continue_()

    page.route("**/api/**", route_handler)
    page.goto("http://127.0.0.1:5173", wait_until="networkidle")
    page.locator("#memory").fill("I remember a warm family evening with my grandparents.")
    page.get_by_role("button", name="Create my soundtrack").click()
    page.get_by_role("button", name="Save to Memory Vault").click()
    assert saved["value"] is True
    assert page.get_by_text("Saved to Memory Vault (#42)").is_visible()
    page.get_by_role("button", name="Memory vault", exact=True).click()
    page.get_by_label("Search memories").fill("family")
    page.get_by_role("button", name="Search vault").click()
    assert page.get_by_role("heading", name="Summer Family Memory").is_visible()
    page.get_by_role("button", name="Delete Summer Family Memory").click()
    browser.close()

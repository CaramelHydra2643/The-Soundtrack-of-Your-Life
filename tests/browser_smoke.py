from playwright.sync_api import sync_playwright


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:5173", wait_until="networkidle")
    assert page.get_by_role("heading", name="Your life has a soundtrack.").is_visible()
    assert page.locator("#memory").is_visible()
    assert page.get_by_role("button", name="Type").is_visible()
    assert page.get_by_role("button", name="Voice").is_visible()
    page.get_by_role("button", name="Voice").click()
    assert page.get_by_text("Speech language").is_visible()
    assert page.locator("#memory").is_visible()
    page.screenshot(path="tests/browser_smoke.png", full_page=True)
    browser.close()

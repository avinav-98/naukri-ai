from threading import local

from backend.automation.playwright_setup import get_playwright


_state = local()


def get_browser():
    """
    Keep one browser per thread to avoid cross-thread Playwright crashes.
    """
    browser = getattr(_state, "browser", None)
    if browser is None:
        playwright = get_playwright()
        browser = playwright.chromium.launch(headless=False, slow_mo=50)
        _state.browser = browser
    return browser


def close_browser_for_current_thread():
    browser = getattr(_state, "browser", None)
    if browser is not None:
        browser.close()
        _state.browser = None


def new_page():
    browser = get_browser()
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0",
    )
    page = context.new_page()
    return page

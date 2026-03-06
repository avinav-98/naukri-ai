from threading import local

from playwright.sync_api import Playwright, sync_playwright


_state = local()


def get_playwright() -> Playwright:
    """
    Keep one Playwright instance per thread.
    Sync Playwright objects are not safe to share across threads.
    """
    if not hasattr(_state, "playwright") or _state.playwright is None:
        _state.playwright = sync_playwright().start()
    return _state.playwright


def stop_playwright_for_current_thread():
    playwright = getattr(_state, "playwright", None)
    if playwright is not None:
        playwright.stop()
        _state.playwright = None

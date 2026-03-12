from threading import local
import os

from backend.automation.playwright_setup import get_playwright


_state = local()


def _is_headless() -> bool:
    # Default to headed mode for local interactive login flows.
    # Set PLAYWRIGHT_HEADLESS=true in server/container environments.
    value = (os.getenv("PLAYWRIGHT_HEADLESS", "false") or "false").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _launch_args():
    return [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",
    ]


def _launch_candidates():
    explicit_channel = (os.getenv("PLAYWRIGHT_BROWSER_CHANNEL", "") or "").strip().lower()
    candidates = []

    if explicit_channel:
        candidates.append({"channel": explicit_channel})
    elif os.name == "nt":
        # Prefer locally installed browsers on Windows to avoid bundled Chromium-specific network issues.
        candidates.append({"channel": "chrome"})
        candidates.append({"channel": "msedge"})

    # Final fallback: bundled Playwright Chromium.
    candidates.append({})
    return candidates


def get_browser():
    """
    Keep one browser per thread to avoid cross-thread Playwright crashes.
    """
    browser = getattr(_state, "browser", None)
    if browser is None:
        playwright = get_playwright()
        last_error = None
        for candidate in _launch_candidates():
            launch_kwargs = {
                "headless": _is_headless(),
                "args": _launch_args(),
                **candidate,
            }
            try:
                label = candidate.get("channel", "playwright-chromium")
                print(f"[BROWSER] Launching via {label} (headless={launch_kwargs['headless']})")
                browser = playwright.chromium.launch(**launch_kwargs)
                print(f"[BROWSER] Launch success via {label}")
                break
            except Exception as exc:
                label = candidate.get("channel", "playwright-chromium")
                print(f"[BROWSER] Launch failed via {label}: {exc}")
                last_error = exc
                browser = None
        if browser is None and last_error is not None:
            raise last_error
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

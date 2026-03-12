from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import save_session

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_HOME_URL = "https://www.naukri.com"


def _is_logged_in(page):
    login_btn = page.query_selector("a:has-text('Login')")
    return login_btn is None


def _first_visible(page, selectors):
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=3000)
            return locator
        except Exception:
            continue
    return None


def _safe_goto(page, url: str, label: str):
    try:
        page.goto(url, wait_until="commit", timeout=15000)
        page.wait_for_timeout(2500)
        print(f"[NAUKRI_LOGIN] {label}: {page.url}")
        return True
    except Exception as exc:
        print(f"[NAUKRI_LOGIN] {label} failed: {exc}")
        return False


def _all_frames(page):
    try:
        return page.frames
    except Exception:
        return [page]


def _first_visible_across_frames(page, selectors):
    for frame in _all_frames(page):
        locator = _first_visible(frame, selectors)
        if locator:
            return frame, locator
    return None, None


def _debug_inputs(page):
    seen = []
    for frame in _all_frames(page):
        try:
            handles = frame.query_selector_all("input")
        except Exception:
            handles = []
        for handle in handles[:12]:
            try:
                item = {
                    "frame": frame.url[:120],
                    "type": (handle.get_attribute("type") or "").strip(),
                    "name": (handle.get_attribute("name") or "").strip(),
                    "id": (handle.get_attribute("id") or "").strip(),
                    "placeholder": (handle.get_attribute("placeholder") or "").strip(),
                }
                seen.append(item)
            except Exception:
                continue
    return seen


def _page_debug_summary(page):
    try:
        title = (page.title() or "").strip()
    except Exception:
        title = ""
    try:
        body_text = (page.locator("body").inner_text(timeout=1500) or "").strip()
    except Exception:
        body_text = ""
    compact_body = " ".join(body_text.split())[:400]
    return {"title": title, "body_preview": compact_body}


def _extract_login_error(page):
    selectors = [
        ".server-err",
        ".err-msg",
        ".error-msg",
        ".formError",
        "[data-testid='login-error']",
        "text=/invalid|incorrect|captcha|verify|blocked|try again/i",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=500):
                text = (locator.inner_text(timeout=500) or "").strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _detect_challenge(page):
    challenge_selectors = [
        "iframe[title*='captcha']",
        "iframe[src*='captcha']",
        "text=/captcha|verify you are human|security check|one time password|otp/i",
    ]
    for selector in challenge_selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def _dismiss_home_overlays(page):
    selectors = [
        "button:has-text('Got it')",
        "button:has-text('No Thanks')",
        "button:has-text('Close')",
        "[aria-label='close']",
        ".crossIcon",
        ".ico-close",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=400):
                locator.click(timeout=1000)
                page.wait_for_timeout(250)
        except Exception:
            continue


def _locate_login_surface(page):
    password_selectors = [
        "input[type='password']",
        "input[placeholder*='Password']",
        "input[placeholder*='password']",
        "input[autocomplete='current-password']",
        "input[name='password']",
        "#passwordField",
    ]
    scoped_email_selectors = [
        "form:has(input[type='password']) input[type='email']",
        "form:has(input[type='password']) input[name='email']",
        "form:has(input[type='password']) input[name='username']",
        "form:has(input[type='password']) input[name='login']",
        "form:has(input[type='password']) input[name='userName']",
        "form:has(input[type='password']) input[autocomplete='username']",
        "form:has(input[type='password']) input[placeholder*='Email']",
        "form:has(input[type='password']) input[placeholder*='email']",
        "form:has(input[type='password']) input[placeholder*='Username']",
        "form:has(input[type='password']) input[placeholder*='username']",
        "form:has(input[type='password']) input[type='text']",
        "div:has(input[type='password']) input[type='email']",
        "div:has(input[type='password']) input[name='email']",
        "div:has(input[type='password']) input[name='username']",
        "div:has(input[type='password']) input[autocomplete='username']",
        "div:has(input[type='password']) input[type='text']",
        "#usernameField",
    ]
    for frame in _all_frames(page):
        password_input = _first_visible(frame, password_selectors)
        if not password_input:
            continue
        email_input = _first_visible(frame, scoped_email_selectors)
        return frame, email_input, frame, password_input
    return None, None, None, None


def _open_login_surface(page):
    print("[NAUKRI_LOGIN] Opening login page...")
    _safe_goto(page, NAUKRI_HOME_URL, "Opened homepage")
    _dismiss_home_overlays(page)

    login_trigger_selectors = [
        "a[title='Login']",
        "a:has-text('Login')",
        "button:has-text('Login')",
        "div:has-text('Login')",
        "[data-ga-track*='login']",
        "[data-ga-track*='Login']",
    ]

    trigger = None
    for selector in login_trigger_selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1200):
                trigger = locator
                break
        except Exception:
            continue

    if not trigger:
        print("[NAUKRI_LOGIN] Homepage login trigger not found. Trying direct login URL...")
        _safe_goto(page, NAUKRI_LOGIN_URL, "Opened direct login page")
        email_frame, email_input, password_frame, password_input = _locate_login_surface(page)
        return page, email_frame, email_input, password_frame, password_input

    popup_page = None
    try:
        with page.expect_popup(timeout=4000) as popup_info:
            trigger.click(timeout=3000)
        popup_page = popup_info.value
        popup_page.wait_for_load_state("domcontentloaded", timeout=10000)
        popup_page.wait_for_timeout(2000)
        target_page = popup_page
        print(f"[NAUKRI_LOGIN] Login opened in popup: {target_page.url}")
    except Exception:
        try:
            trigger.click(timeout=3000)
        except Exception:
            page.evaluate("(el) => el.click()", trigger.element_handle())
        page.wait_for_timeout(2500)
        target_page = page
        print(f"[NAUKRI_LOGIN] Login opened inline/current page: {target_page.url}")

    email_frame, email_input, password_frame, password_input = _locate_login_surface(target_page)
    if not email_input or not password_input:
        print("[NAUKRI_LOGIN] Homepage flow did not expose fields. Trying direct login URL...")
        _safe_goto(page, NAUKRI_LOGIN_URL, "Opened direct login page")
        email_frame, email_input, password_frame, password_input = _locate_login_surface(page)
        target_page = page
    return target_page, email_frame, email_input, password_frame, password_input


def login_with_credentials(user_id: int, naukri_id: str, naukri_password: str):
    context = None
    try:
        print("[NAUKRI_LOGIN] Launching browser...")
        browser = get_browser()
        context = browser.new_context()
        page = context.new_page()
        target_page, email_frame, email_input, password_frame, password_input = _open_login_surface(page)

        print("[NAUKRI_LOGIN] Entering credentials...")
        if not email_input or not password_input:
            discovered = _debug_inputs(target_page)
            page_debug = _page_debug_summary(target_page)
            message = (
                f"Could not find Naukri login fields. Current URL: {target_page.url}. "
                f"Title: {page_debug.get('title', '')}. "
                f"Body preview: {page_debug.get('body_preview', '')}. "
                f"Discovered inputs: {discovered}"
            )
            print(f"[NAUKRI_LOGIN] {message}")
            return False, message

        email_input.click(timeout=2000)
        email_input.fill("")
        email_input.type(naukri_id, delay=40)
        password_input.click(timeout=2000)
        password_input.fill("")
        password_input.type(naukri_password, delay=40)

        submit_frame, submit_btn = _first_visible_across_frames(
            target_page,
            [
                "button[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                "button:has-text('Continue')",
                "input[type='submit']",
            ],
        )

        if submit_btn:
            submit_btn.click(timeout=3000)
        else:
            active_frame = password_frame or email_frame or target_page
            active_frame.keyboard.press("Enter")

        target_page.wait_for_timeout(5000)

        if _detect_challenge(target_page):
            message = "Naukri presented a captcha or verification challenge. Complete it manually and try again."
            print(f"[NAUKRI_LOGIN] {message}")
            return False, message

        inline_error = _extract_login_error(target_page)
        if inline_error:
            message = f"Naukri rejected the login: {inline_error}"
            print(f"[NAUKRI_LOGIN] {message}")
            return False, message

        current_url = target_page.url
        if "nlogin" in current_url:
            message = f"Naukri login did not complete. Current URL: {current_url}"
            print(f"[NAUKRI_LOGIN] {message}")
            return False, message

        target_page.goto(NAUKRI_HOME_URL, wait_until="domcontentloaded")
        target_page.wait_for_timeout(3000)

        if not _is_logged_in(target_page):
            inline_error = _extract_login_error(target_page)
            if inline_error:
                message = f"Naukri rejected the login: {inline_error}"
                print(f"[NAUKRI_LOGIN] {message}")
                return False, message
            message = "Invalid Naukri credentials or blocked login flow"
            print(f"[NAUKRI_LOGIN] {message}")
            return False, message

        save_session(context, user_id=user_id)
        print("[NAUKRI_LOGIN] Session linked successfully.")
        return True, "Naukri session linked successfully"
    except Exception as exc:
        print(f"[NAUKRI_LOGIN] Login failed: {exc}")
        return False, f"Login flow failed: {exc}"
    finally:
        if context:
            context.close()

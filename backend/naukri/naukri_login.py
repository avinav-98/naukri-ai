from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import save_session

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"


def _is_logged_in(page):
    login_btn = page.query_selector("a:has-text('Login')")
    return login_btn is None


def login_with_credentials(user_id: int, naukri_id: str, naukri_password: str):
    context = None
    try:
        print("[NAUKRI_LOGIN] Launching browser...")
        browser = get_browser()
        context = browser.new_context()
        page = context.new_page()

        print("[NAUKRI_LOGIN] Opening login page...")
        page.goto(NAUKRI_LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        email_selectors = ["input[type='email']", "input[placeholder*='Email']", "#usernameField"]
        password_selectors = ["input[type='password']", "input[placeholder*='Password']", "#passwordField"]

        print("[NAUKRI_LOGIN] Entering credentials...")
        email_filled = False
        for selector in email_selectors:
            el = page.query_selector(selector)
            if el:
                el.fill(naukri_id)
                email_filled = True
                break

        password_filled = False
        for selector in password_selectors:
            el = page.query_selector(selector)
            if el:
                el.fill(naukri_password)
                password_filled = True
                break

        if not email_filled or not password_filled:
            return False, "Could not find login form fields on Naukri page"

        submit_btn = page.query_selector(
            "button[type='submit'], button:has-text('Login'), button:has-text('Sign in')"
        )

        if submit_btn:
            submit_btn.click()
        else:
            page.keyboard.press("Enter")

        page.wait_for_timeout(5000)
        page.goto("https://www.naukri.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not _is_logged_in(page):
            return False, "Invalid Naukri credentials or blocked login flow"

        save_session(context, user_id=user_id)
        print("[NAUKRI_LOGIN] Session linked successfully.")
        return True, "Naukri session linked successfully"
    except Exception as exc:
        print(f"[NAUKRI_LOGIN] Login failed: {exc}")
        return False, f"Login flow failed: {exc}"
    finally:
        if context:
            context.close()

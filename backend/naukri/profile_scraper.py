from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session


def scrape_profile(user_id=1):

    browser = get_browser()

    context = browser.new_context()

    load_session(context, user_id)

    page = context.new_page()

    page.goto("https://www.naukri.com/mnjuser/profile")

    page.wait_for_timeout(3000)

    name = page.query_selector("span.name")

    if name:

        return name.inner_text()

    return "Unknown"
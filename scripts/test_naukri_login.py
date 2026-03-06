from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import save_session


USER_ID = 1


browser = get_browser()

context = browser.new_context()

page = context.new_page()

page.goto("https://www.naukri.com")

input("Login manually and press ENTER")

save_session(context, USER_ID)
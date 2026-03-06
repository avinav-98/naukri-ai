import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session


browser = get_browser()

context = browser.new_context()

load_session(context)

page = context.new_page()

page.goto("https://www.naukri.com/mnjuser/homepage")

input("Check if you are logged in.")
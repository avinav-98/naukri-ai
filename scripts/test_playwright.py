import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.automation.browser_manager import new_page


page = new_page()

page.goto("https://example.com")

input("Browser running. Press Enter to close.")
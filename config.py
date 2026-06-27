import os
from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = os.getenv("REI_LOGIN_URL", "https://my.reiblackbook.com/services/account/login?block=")
EMAIL = os.getenv("REI_EMAIL", "")
PASSWORD = os.getenv("REI_PASSWORD", "")
HEADLESS = os.getenv("REI_HEADLESS", "true").lower() == "true"
SCREENSHOT_DIR = os.getenv("REI_SCREENSHOT_DIR", "screenshots")
TIMEOUT = int(os.getenv("REI_TIMEOUT", "30000"))

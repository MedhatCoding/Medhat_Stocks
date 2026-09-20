import os

APP_NAME = "Medhat Stocks AI"
APP_VERSION = "2.0"
MARKET = "EGX"
TIMEZONE = "Africa/Cairo"

EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")
OANOR_API_KEY = os.getenv("OANOR_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# The 113-stock target universe agreed for the product.
# The app ships with a dated Sharia reference list and supports updating it
# through the SHARIA_SYMBOLS secret without changing the code.
STOCK_UNIVERSE_SIZE = 113
OPPORTUNITY_SCORE_MIN = 0
OPPORTUNITY_SCORE_MAX = 100

SHOW_TECHNICAL_DEFAULT = False

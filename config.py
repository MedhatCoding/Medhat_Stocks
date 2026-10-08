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

# The displayed Sharia universe is sourced from sharia_universe.py; keep this
# value only as a backwards-compatible fallback for older UI code.
STOCK_UNIVERSE_SIZE = 96
OPPORTUNITY_SCORE_MIN = 0
OPPORTUNITY_SCORE_MAX = 100

SHOW_TECHNICAL_DEFAULT = False

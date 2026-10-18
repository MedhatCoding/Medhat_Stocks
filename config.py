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

# The universe size is derived from the maintained reference list at runtime.
# Do not hard-code 96: updates to the verified list must flow through the app.
STOCK_UNIVERSE_SIZE = 0

# Optional extra historical provider. Leave unset until EGX symbol coverage,
# daily history quality, and free-tier terms have been verified with real data.
EGXAPI_KEY = os.getenv("EGXAPI_KEY", "")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
OPPORTUNITY_SCORE_MIN = 0
OPPORTUNITY_SCORE_MAX = 100

SHOW_TECHNICAL_DEFAULT = False

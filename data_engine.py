import os
import requests
from datetime import datetime, timezone


class DataEngine:
    """محرك بيانات البورصة المصرية."""

    BASE_URL = "https://eodhd.com/api"

    def __init__(self):
        self.eodhd_api_key = os.getenv("EODHD_API_KEY", "")
        self.oanor_api_key = os.getenv("OANOR_API_KEY", "")

    def health_check(self):
        return {
            "eodhd_configured": bool(self.eodhd_api_key),
            "oanor_configured": bool(self.oanor_api_key),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_egx_symbols(self):
        """الحصول على قائمة الأسهم المتاحة في EGX."""
        if not self.eodhd_api_key:
            return {
                "success": False,
                "error": "EODHD_API_KEY غير موجود",
                "data": [],
            }

        url = f"{self.BASE_URL}/exchange-symbol-list/NILX"

        try:
            response = requests.get(
                url,
                params={
                    "api_token": self.eodhd_api_key,
                    "fmt": "json",
                },
                timeout=30,
            )

            response.raise_for_status()

            return {
                "success": True,
                "data": response.json(),
            }

        except requests.RequestException as exc:
            return {
                "success": False,
                "error": str(exc),
                "data": [],
            }

    def get_stock_history(self, symbol, days=365):
        """جلب التاريخ اليومي لسهم من EGX."""

        if not self.eodhd_api_key:
            return {
                "success": False,
                "error": "EODHD_API_KEY غير موجود",
                "data": [],
            }

        symbol = symbol.upper().strip()

        if "." not in symbol:
            symbol = f"{symbol}.NILX"

        url = f"{self.BASE_URL}/eod/{symbol}"

        try:
            response = requests.get(
                url,
                params={
                    "api_token": self.eodhd_api_key,
                    "fmt": "json",
                    "period": "d",
                    "order": "d",
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                data = data[:days]

            return {
                "success": True,
                "symbol": symbol,
                "data": data,
            }

        except requests.RequestException as exc:
            return {
                "success": False,
                "symbol": symbol,
                "error": str(exc),
                "data": [],
            }

    def get_latest_price(self, symbol):
        """الحصول على آخر سعر إغلاق متاح."""

        result = self.get_stock_history(symbol, days=1)

        if not result["success"] or not result["data"]:
            return {
                "success": False,
                "symbol": symbol,
                "price": None,
                "error": result.get("error", "لا توجد بيانات"),
            }

        row = result["data"][0]

        return {
            "success": True,
            "symbol": result["symbol"],
            "date": row.get("date"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
        }


data_engine = DataEngine()

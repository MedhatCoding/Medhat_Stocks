import os
import requests
from datetime import datetime, timezone


class DataEngine:
    """Central market-data engine for Medhat Stocks AI."""

    def __init__(self):
        self.eodhd_api_key = os.getenv("EODHD_API_KEY", "")
        self.oanor_api_key = os.getenv("OANOR_API_KEY", "")

    def health_check(self):
        return {
            "eodhd_configured": bool(self.eodhd_api_key),
            "oanor_configured": bool(self.oanor_api_key),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_status(self):
        status = self.health_check()

        return {
            "status": "ready",
            "providers": status,
        }

    @staticmethod
    def safe_request(url, params=None, timeout=20):
        try:
            response = requests.get(
                url,
                params=params or {},
                timeout=timeout,
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
                "data": None,
            }

    def get_stock_data(self, symbol):
        """
        Placeholder for the unified stock-data interface.

        The actual EGX provider endpoints will be connected
        in the next stage without changing the rest of the app.
        """

        return {
            "symbol": symbol.upper(),
            "success": False,
            "message": "Market data provider is not connected yet.",
        }


data_engine = DataEngine()

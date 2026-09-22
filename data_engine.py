import os
import re
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st

from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE, REFERENCE_SOURCE
from ml_engine import train_and_predict
from recommendation_journal import adaptive_feedback, record_opportunity


def get_secret(name):
    """Read a secret from Streamlit Secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, "")


class DataEngine:
    """EGX data + technical analysis engine."""

    BASE_URL = "https://eodhd.com/api"
    EGX_EXCHANGE = "EGX"

    def __init__(self):
        self.eodhd_api_key = get_secret("EODHD_API_KEY")
        self.oanor_api_key = get_secret("OANOR_API_KEY")
        self.gemini_api_key = get_secret("GEMINI_API_KEY")
        self.gemini_model = get_secret("GEMINI_MODEL") or "gemini-2.5-flash"

    ARABIC_COMPANY_NAMES = {
        "AALR":"العربية للأدوية والصناعات الكيماوية",
        "ACGC":"العربية لحليج الأقطان",
        "ACRO":"كريستال أسيل للدهانات والكيماويات",
        "ADIB":"مصرف أبو ظبي الإسلامي - مصر",
        "AIFI":"العربية للاستثمارات المالية",
        "AITG":"أجواء للصناعات الغذائية",
        "AIVCB":"العربية للاستثمارات والتنمية",
        "ALUM":"الألومنيوم العربية",
        "AMER":"عامر جروب",
        "AMES":"أسمنت سيناء",
        "AMOC":"الإسكندرية للزيوت المعدنية",
        "AMIA":"الملتقى العربي للاستثمارات",
        "APSW":"العربية وبولفارا للغزل والنسيج - يونيراب",
        "ASHC":"شركة مجموعة السلام القابضة",
        "DPKP":"دي بي كي للصناعات الدوائية",
        "EALR":"العربية لاستصلاح الأراضي",
        "APPC":"العربية لمنتجات الألبان",
        "ARCC":"العربية للأسمنت",
        "ARVA":"العربية لمنتجات الأدوية",
        "ATLC":"التوفيق للتأجير التمويلي",
        "ATQA":"الإسكندرية لتداول الحاويات والبضائع",
        "AXPH":"الإسكندرية للأدوية والصناعات الكيماوية",
        "BIOC":"جلاكسو سميثكلاين مصر",
        "BTFH":"بلتون القابضة",
        "CAED":"القاهرة للأدوية والصناعات الكيماوية",
        "CLHO":"مستشفى كليوباترا",
        "COSG":"القاهرة للزيوت والصابون",
        "CPCI":"القاهرة للاستثمار والتنمية العقارية",
        "DAPH":"الداو للتنمية العقارية",
        "DCRC":"دايس للملابس الجاهزة",
        "EFIC":"المالية والصناعية المصرية",
        "EFID":"إي فاينانس للاستثمارات المالية والرقمية",
        "EGAL":"مصر للألومنيوم",
        "EGAS":"المصرية للغازات الطبيعية",
        "ELKA":"القاهرة للاستثمار والتنمية",
        "ELNA":"النصر للأعمال المدنية",
        "EMRI":"إميرالد للاستثمار العقاري",
        "ETRS":"المصرية لخدمات النقل",
        "FAIT":"بنك فيصل الإسلامي المصري - بالجنيه",
        "FAITA":"بنك فيصل الإسلامي المصري - بالدولار",
        "GGCC":"جي بي كورب",
        "GIHD":"غاز مصر",
        "GMCI":"جولدن تكس للأصواف",
        "GSSC":"القلعة للاستثمارات المالية",
        "GTHE":"الجيزة العامة للمقاولات",
        "IDHC":"ابن سينا فارما",
        "IFAP":"الإسماعيلية الوطنية للصناعات الغذائية",
        "INFI":"إنفينيتي كابيتال",
        "IRON":"عز الدخيلة للصلب - الإسكندرية",
        "ISMA":"الإسماعيلية مصر للدواجن",
        "ISMQ":"الحديد والصلب للمناجم والمحاجر",
        "JUFO":"جهينة للصناعات الغذائية",
        "KABO":"النيل للكبريت والمطاط",
        "MAAL":"المصرية للمنتجعات السياحية",
        "MBEG":"مدينة مصر للإسكان والتعمير",
        "MASR":"مدينة مصر للإسكان والتعمير",
        "MBSC":"مصر بني سويف للأسمنت",
        "MCQE":"مصر للأسمنت - قنا",
        "MCRO":"مصر لصناعة الكيماويات",
        "MEPA":"مينا فارم للأدوية والصناعات الكيماوية",
        "MFPC":"أبو قير للأسمدة والصناعات الكيماوية",
        "MICH":"مصر لصناعة الكيماويات",
        "MILS":"مطاحن مصر الوسطى",
        "MOED":"مصر لإنتاج الأسمدة - موبكو",
        "MPCO":"المنصورة للدواجن",
        "MTIE":"إم تي آي",
        "NCEM":"شمال الصعيد للتنمية والإنتاج الزراعي",
        "NCGC":"النيل لحليج الأقطان",
        "NDRL":"الوادي العالمية للاستثمار والتنمية",
        "NEDA":"النصر للأعمال المدنية",
        "NIPH":"النيل للأدوية والصناعات الكيماوية",
        "NOAF":"شمال أفريقيا للاستثمار العقاري",
        "ORAS":"أوراسكوم كونستراكشون",
        "PACH":"باكين",
        "PHDC":"بالم هيلز للتعمير",
        "PRDC":"بروبرتيز للتنمية العقارية",
        "RACC":"راية القابضة للاستثمارات المالية",
        "RMDA":"العاشر من رمضان للصناعات الدوائية",
        "RREI":"الحديد والصلب المصرية - سابقًا",
        "RUBX":"روبكس العالمية لتصنيع البلاستيك والأكريليك",
        "SAUD":"المصرية للمنتجعات السياحية",
        "SCEM":"أسمنت سيناء",
        "SIPC":"سبينالكس",
        "SMCS":"سماد مصر",
        "SMFR":"سماد مصر - إيجيفرت",
        "SPIN":"الإسكندرية الوطنية للاستثمارات المالية",
        "SPMD":"سبينالكس",
        "SUCE":"السويس للأسمنت",
        "SUGR":"الدلتا للسكر",
        "SVCE":"جنوب الوادي للأسمنت",
        "SWDY":"السويدي إليكتريك",
        "TALM":"تعليم لخدمات الإدارة",
        "TRSI":"العربية للخزف - سيراميكا ريماس",
        "VODE":"فودافون مصر",
        "WATP":"وادى كوم أمبو لاستصلاح الأراضي",
        "ZEOT":"الزيوت المستخلصة ومنتجاتها",
    }

    @classmethod
    def arabic_company_name(cls, symbol, fallback="اسم الشركة غير متاح"):
        code = cls.display_symbol(symbol)
        return cls.ARABIC_COMPANY_NAMES.get(code, fallback)

    @staticmethod
    def normalize_symbol(symbol):
        value = (symbol or "").strip().upper()
        value = re.sub(r"\s+", "", value)
        if not value:
            return ""
        if "." not in value:
            value = f"{value}.EGX"
        return value

    @staticmethod
    def display_symbol(symbol):
        return (symbol or "").split(".")[0].upper()

    def health_check(self):
        return {
            "eodhd_configured": bool(self.eodhd_api_key),
            "oanor_configured": bool(self.oanor_api_key),
            "gemini_configured": bool(self.gemini_api_key),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get(self, path, params=None, timeout=30):
        if not self.eodhd_api_key:
            return {"success": False, "error": "EODHD_API_KEY غير موجود"}
        query = dict(params or {})
        query["api_token"] = self.eodhd_api_key
        query.setdefault("fmt", "json")
        try:
            response = requests.get(
                f"{self.BASE_URL}/{path.lstrip('/')}",
                params=query,
                timeout=timeout,
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 404:
                return {"success": False, "error": "بيانات هذا المسار غير متاحة حاليًا من مزود الأسعار."}
            if status in (401, 403):
                return {"success": False, "error": "مفتاح مزود بيانات الأسعار غير صالح أو غير مصرح لهذا الطلب."}
            return {"success": False, "error": f"تعذر جلب بيانات الأسعار (HTTP {status or 'error'})."}
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc)}
        except ValueError as exc:
            return {"success": False, "error": f"استجابة غير صالحة من مزود البيانات: {exc}"}

    def _oanor_get(self, path, params=None, timeout=20):
        if not self.oanor_api_key:
            return {"success": False, "error": "OANOR_API_KEY غير موجود"}
        try:
            response = requests.get(
                f"https://api.oanor.com/{path.lstrip('/')}",
                params=dict(params or {}),
                headers={"x-oanor-key": self.oanor_api_key},
                timeout=timeout,
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc)}
        except ValueError as exc:
            return {"success": False, "error": f"استجابة OANOR غير صالحة: {exc}"}

    def get_live_quote(self, symbol):
        code = self.display_symbol(symbol)
        result = self._oanor_get("egx-api/v1/quote", {"symbol": code}, timeout=15)
        if not result["success"]:
            return result
        data = result["data"]
        rows = data.get("data") if isinstance(data, dict) else data
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            return {"success": False, "error": "لا توجد تسعيرة حية"}
        return {"success": True, "data": rows[0]}

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_egx_symbols(_self):
        result = _self._get(f"exchange-symbol-list/{_self.EGX_EXCHANGE}")
        if not result["success"]:
            return result
        data = result["data"]
        if not isinstance(data, list):
            return {"success": False, "error": "قائمة EGX غير صالحة", "data": []}
        cleaned = []
        for row in data:
            if isinstance(row, dict):
                code = str(row.get("Code") or row.get("code") or "").upper()
                name = row.get("Name") or row.get("name") or ""
                if code:
                    cleaned.append({"code": code, "name": str(name)})
        return {"success": True, "data": cleaned}

    def search_symbols(self, query, limit=12):
        query = (query or "").strip().upper()
        if not query:
            return []
        result = self.get_egx_symbols()
        if not result["success"]:
            return []
        rows = result["data"]
        ranked = []
        for row in rows:
            code = row["code"].upper()
            name = row["name"].upper()
            if code == query:
                rank = 0
            elif code.startswith(query):
                rank = 1
            elif query in code:
                rank = 2
            elif query in name:
                rank = 3
            else:
                continue
            ranked.append((rank, code, row["name"]))
        ranked.sort(key=lambda x: (x[0], x[1]))
        return [{"symbol": code, "name": name} for _, code, name in ranked[:limit]]

    def _yahoo_history(self, symbol, period="2y"):
        """Fallback EGX daily history via Yahoo Finance when EODHD is unavailable."""
        code = self.display_symbol(symbol)
        yahoo_symbol = f"{code}.CA"
        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={"range": period, "interval": "1d", "events": "history"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                return {"success": False, "error": "لا توجد بيانات تاريخية لهذا السهم من المصدر البديل.", "data": []}
            item = result[0]
            timestamps = item.get("timestamp") or []
            quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
            rows = []
            for i, ts in enumerate(timestamps):
                def at(key):
                    values = quote.get(key) or []
                    return values[i] if i < len(values) else None
                if at("close") is None:
                    continue
                rows.append({
                    "date": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"),
                    "open": at("open"), "high": at("high"), "low": at("low"),
                    "close": at("close"), "volume": at("volume"),
                })
            rows.sort(key=lambda x: x["date"], reverse=True)
            meta = item.get("meta") or {}
            return {"success": bool(rows), "symbol": self.normalize_symbol(symbol),
                    "data": rows, "name_en": meta.get("longName") or meta.get("shortName") or "",
                    "provider": "Yahoo Finance fallback"}
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            return {"success": False, "symbol": self.normalize_symbol(symbol), "error": str(exc), "data": []}

    @st.cache_data(ttl=900, show_spinner=False)
    def get_stock_history(_self, symbol, days=365):
        normalized = _self.normalize_symbol(symbol)
        if not normalized:
            return {"success": False, "error": "رمز السهم غير صالح", "data": []}
        result = _self._get(
            f"eod/{normalized}",
            {"period": "d", "order": "d"},
            timeout=30,
        )
        if not result["success"]:
            fallback = _self._yahoo_history(normalized)
            if fallback.get("success"):
                return fallback
            return {"success": False, "symbol": normalized, "error": result["error"], "data": []}
        data = result["data"]
        if not isinstance(data, list):
            return {"success": False, "symbol": normalized, "error": "لا توجد بيانات تاريخية", "data": []}
        return {"success": True, "symbol": normalized, "data": data[:max(30, int(days))]}

    @st.cache_data(ttl=900, show_spinner=False)
    def get_fundamentals(_self, symbol):
        normalized = _self.normalize_symbol(symbol)
        if not normalized:
            return {"success": False, "error": "رمز السهم غير صالح", "data": {}}
        result = _self._get(f"v1.1/fundamentals/{normalized}", timeout=30)
        if not result["success"]:
            return {"success": False, "symbol": normalized, "error": result["error"], "data": {}}
        data = result["data"]
        return {"success": True, "symbol": normalized, "data": data if isinstance(data, dict) else {}}

    def get_latest_price(self, symbol):
        result = self.get_stock_history(symbol, days=5)
        if not result["success"] or not result["data"]:
            return {
                "success": False,
                "symbol": self.normalize_symbol(symbol),
                "price": None,
                "error": result.get("error", "لا توجد بيانات"),
            }
        row = result["data"][0]
        previous = result["data"][1] if len(result["data"]) > 1 else {}
        close = self._num(row.get("close"))
        prev_close = self._num(previous.get("close"))
        change = close - prev_close if close is not None and prev_close is not None else None
        change_pct = (change / prev_close * 100) if change is not None and prev_close else None
        return {
            "success": True,
            "symbol": result["symbol"],
            "date": row.get("date"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "previous_close": previous.get("close"),
            "change": change,
            "change_pct": change_pct,
        }

    @staticmethod
    def _num(value):
        try:
            if value is None or value == "":
                return None
            number = float(value)
            return number if np.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _series(data):
        frame = pd.DataFrame(data or [])
        if frame.empty:
            return frame
        for col in ["open", "high", "low", "close", "adjusted_close", "volume"]:
            if col in frame:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame["date"] = pd.to_datetime(frame.get("date"), errors="coerce")
        frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
        return frame

    def analyze_stock(self, symbol):
        history = self.get_stock_history(symbol, days=365)
        if not history["success"] or not history["data"]:
            return {"success": False, "error": history.get("error", "لا توجد بيانات")}

        frame = self._series(history["data"])
        if len(frame) < 30:
            return {"success": False, "error": "البيانات التاريخية المتاحة أقل من 30 جلسة"}

        close = frame["close"]
        volume = frame["volume"] if "volume" in frame else pd.Series(dtype=float)

        frame["sma20"] = close.rolling(20).mean()
        frame["sma50"] = close.rolling(50).mean()
        frame["sma200"] = close.rolling(200).mean()
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        frame["rsi14"] = 100 - (100 / (1 + rs))
        tr_parts = [
            frame["high"] - frame["low"],
            (frame["high"] - frame["close"].shift()).abs(),
            (frame["low"] - frame["close"].shift()).abs(),
        ]
        frame["atr14"] = pd.concat(tr_parts, axis=1).max(axis=1).rolling(14).mean()
        frame["return_20d"] = close.pct_change(20) * 100
        frame["return_60d"] = close.pct_change(60) * 100
        frame["volatility20"] = close.pct_change().rolling(20).std() * np.sqrt(252) * 100
        if not volume.empty:
            frame["volume_avg20"] = volume.rolling(20).mean()
            frame["volume_ratio"] = volume / frame["volume_avg20"]
        else:
            frame["volume_avg20"] = np.nan
            frame["volume_ratio"] = np.nan

        latest = frame.iloc[-1]
        last_close = self._num(latest["close"])
        sma20 = self._num(latest.get("sma20"))
        sma50 = self._num(latest.get("sma50"))
        sma200 = self._num(latest.get("sma200"))
        rsi = self._num(latest.get("rsi14"))
        atr = self._num(latest.get("atr14"))
        ret20 = self._num(latest.get("return_20d"))
        ret60 = self._num(latest.get("return_60d"))
        vol20 = self._num(latest.get("volatility20"))
        vol_ratio = self._num(latest.get("volume_ratio"))

        recent = frame.tail(60)
        support = self._num(recent["low"].min())
        resistance = self._num(recent["high"].max())

        trend_points = 0
        if last_close is not None and sma20 is not None:
            trend_points += 20 if last_close > sma20 else 0
        if last_close is not None and sma50 is not None:
            trend_points += 20 if last_close > sma50 else 0
        if sma20 is not None and sma50 is not None:
            trend_points += 15 if sma20 > sma50 else 0
        if sma50 is not None and sma200 is not None:
            trend_points += 15 if sma50 > sma200 else 0
        if ret20 is not None:
            trend_points += 10 if ret20 > 0 else 0
        if ret60 is not None:
            trend_points += 10 if ret60 > 0 else 0
        if rsi is not None:
            trend_points += 10 if 45 <= rsi <= 68 else (5 if 35 <= rsi < 45 else 0)

        risk_points = 0
        if vol20 is not None:
            risk_points += min(35, max(0, vol20 - 15))
        if rsi is not None and rsi > 75:
            risk_points += 25
        if atr is not None and last_close:
            risk_points += min(25, (atr / last_close) * 100)
        if vol_ratio is not None and vol_ratio < 0.5:
            risk_points += 15
        risk_score = int(min(100, round(risk_points)))
        opportunity_score = int(max(0, min(100, round(trend_points - risk_score * 0.35 + 25))))

        if risk_score >= 70:
            status = "مخاطر مرتفعة"
        elif opportunity_score >= 75 and risk_score < 45:
            status = "إيجابي"
        elif opportunity_score >= 55:
            status = "مراقبة"
        else:
            status = "محايد"

        ml = train_and_predict(frame, feedback=adaptive_feedback())
        chart = frame.tail(120)[["date", "close", "sma20", "sma50", "sma200"]].copy()
        chart["date"] = chart["date"].dt.strftime("%Y-%m-%d")

        return {
            "success": True,
            "symbol": history["symbol"],
            "date": str(latest["date"].date()),
            "close": last_close,
            "open": self._num(latest.get("open")),
            "high": self._num(latest.get("high")),
            "low": self._num(latest.get("low")),
            "volume": self._num(latest.get("volume")),
            "previous_close": self._num(frame.iloc[-2]["close"]) if len(frame) > 1 else None,
            "change_pct": ((last_close / self._num(frame.iloc[-2]["close"]) - 1) * 100) if len(frame) > 1 and self._num(frame.iloc[-2]["close"]) else None,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "rsi14": rsi,
            "atr14": atr,
            "return20": ret20,
            "return60": ret60,
            "volatility20": vol20,
            "volume_ratio": vol_ratio,
            "volatility20": vol20,
            "atr_pct": (atr / last_close * 100) if atr and last_close else None,
            "distance_support_pct": ((last_close - support) / last_close * 100) if last_close and support else None,
            "trend20": (last_close / sma20 - 1) if last_close and sma20 else None,
            "trend50": (last_close / sma50 - 1) if last_close and sma50 else None,
            "return60": ret60,
            "support": support,
            "resistance": resistance,
            "opportunity_score": opportunity_score,
            "risk_score": risk_score,
            "status": status,
            "history_rows": len(frame),
            "chart": chart,
            "ml": ml,
        }

    def get_company_snapshot(self, symbol):
        result = self.get_fundamentals(symbol)
        if not result["success"]:
            return result
        data = result["data"]
        general = data.get("General", {}) if isinstance(data, dict) else {}
        highlights = data.get("Highlights", {}) if isinstance(data, dict) else {}
        valuation = data.get("Valuation", {}) if isinstance(data, dict) else {}
        return {
            "success": True,
            "symbol": result["symbol"],
            "name": self.arabic_company_name(result["symbol"], general.get("Name") or general.get("NameLong") or self.display_symbol(result["symbol"])),
            "name_en": general.get("Name") or general.get("NameLong") or self.display_symbol(result["symbol"]),
            "description": general.get("Description") or "",
            "sector": general.get("Sector") or "—",
            "industry": general.get("Industry") or "—",
            "currency": general.get("CurrencyCode") or "EGP",
            "market_cap": highlights.get("MarketCapitalization"),
            "pe": highlights.get("PERatio"),
            "eps": highlights.get("EarningsShare"),
            "dividend_yield": highlights.get("DividendYield"),
            "book_value": highlights.get("BookValue"),
            "beta": highlights.get("Beta"),
            "valuation_pe": valuation.get("TrailingPE") or valuation.get("ForwardPE"),
        }

    def ai_analysis(self, symbol, technical=None, fundamentals=None):
        if not self.gemini_api_key:
            return {"success": False, "error": "GEMINI_API_KEY غير موجود"}
        if technical is None:
            technical = self.analyze_stock(symbol)
            if not technical.get("success"):
                return technical
        payload = {
            "السهم": self.display_symbol(symbol),
            "التاريخ": technical.get("date"),
            "السعر": technical.get("close"),
            "التغير": technical.get("change_pct"),
            "RSI14": technical.get("rsi14"),
            "SMA20": technical.get("sma20"),
            "SMA50": technical.get("sma50"),
            "SMA200": technical.get("sma200"),
            "العائد20جلسة": technical.get("return20"),
            "العائد60جلسة": technical.get("return60"),
            "التذبذب_السنوي_التقريبي": technical.get("volatility20"),
            "نسبة_الحجم": technical.get("volume_ratio"),
            "الدعم": technical.get("support"),
            "المقاومة": technical.get("resistance"),
            "درجة_الفرصة_الحسابية": technical.get("opportunity_score"),
            "درجة_المخاطر_الحسابية": technical.get("risk_score"),
            "القطاع": (fundamentals or {}).get("sector", "غير متاح"),
            "القيمة_السوقية": (fundamentals or {}).get("market_cap"),
            "مكرر_الربحية": (fundamentals or {}).get("pe"),
        }
        system = (
            "أنت محلل أسواق مالية مساعد. حلل البيانات المعطاة فقط ولا تخترع أرقاماً. "
            "اكتب بالعربية المصرية المهنية المختصرة. لا تعطِ أمراً بالشراء أو البيع ولا تتنبأ بسعر. "
            "قسّم الرد إلى: الملخص، الاتجاه الفني، نقاط القوة، المخاطر، ما يجب مراقبته. "
            "اذكر بوضوح أن التحليل معلوماتي وليس توصية استثمارية."
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": system + "\n\nبيانات السهم:\n" + pd.Series(payload).to_json(force_ascii=False)}
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900},
        }
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent",
                params={"key": self.gemini_api_key},
                json=body,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            text = ""
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
            if not text:
                return {"success": False, "error": "لم يُرجع Gemini نصاً"}
            return {"success": True, "text": text}
        except requests.RequestException as exc:
            return {"success": False, "error": f"تعذر الاتصال بمحرك AI: {exc}"}
        except (ValueError, KeyError, TypeError) as exc:
            return {"success": False, "error": f"استجابة AI غير متوقعة: {exc}"}


    def get_news(self, symbol=None, limit=8):
        limit = max(1, min(int(limit), 20))
        if self.oanor_api_key:
            query = self.display_symbol(symbol) if symbol else "Egyptian Exchange EGX stocks"
            oanor = self._oanor_get("news-api/v1/search", {"q": query, "limit": limit, "language": "en"}, timeout=20)
            if oanor["success"]:
                payload = oanor["data"]
                rows = payload.get("articles") if isinstance(payload, dict) else payload
                if isinstance(rows, list):
                    clean = []
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        clean.append({
                            "date": row.get("published_at") or row.get("publishedAt") or row.get("date"),
                            "title": row.get("title") or "",
                            "content": row.get("snippet") or row.get("description") or row.get("content") or "",
                            "link": row.get("url") or row.get("link") or "",
                            "polarity": self._num(row.get("polarity")),
                            "positive": self._num(row.get("positive")),
                            "negative": self._num(row.get("negative")),
                            "source": row.get("publisher") or row.get("source") or "OANOR",
                        })
                    if clean:
                        return {"success": True, "data": clean, "provider": "OANOR"}

        params = {"limit": limit}
        if symbol:
            params["s"] = self.normalize_symbol(symbol)
        result = self._get("news", params=params, timeout=30)
        if not result["success"]:
            return {"success": False, "error": result["error"], "data": []}
        rows = result["data"] if isinstance(result["data"], list) else []
        clean = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sentiment = row.get("sentiment") or {}
            clean.append({
                "date": row.get("date"),
                "title": row.get("title") or "",
                "content": row.get("content") or "",
                "link": row.get("link") or "",
                "polarity": self._num(sentiment.get("polarity")),
                "positive": self._num(sentiment.get("pos")),
                "negative": self._num(sentiment.get("neg")),
                "source": "EODHD",
            })
        return {"success": True, "data": clean, "provider": "EODHD"}

    def get_market_context(self):
        """Return a resilient EGX30 market snapshot.
        Prefer OANOR, then EODHD's index namespace (INDX), then Yahoo's CASE30 index.
        """
        index_candidates = [
            os.getenv("EGX_INDEX_SYMBOL", "EGX30.INDX"),
            "EGX30.INDX",
            "CASE30.INDX",
        ]

        if self.oanor_api_key:
            idx = self._oanor_get("egx-api/v1/index", timeout=15)
            if idx.get("success"):
                payload = idx.get("data") or {}
                row = payload.get("data") if isinstance(payload, dict) else payload
                if isinstance(row, list):
                    row = row[0] if row else {}
                if isinstance(row, dict):
                    close = self._num(row.get("value") or row.get("close") or row.get("price"))
                    if close is not None:
                        return {
                            "success": True, "available": True, "symbol": "EGX30",
                            "date": row.get("date") or row.get("timestamp"),
                            "close": close,
                            "sma20": None, "sma50": None,
                            "return20": self._num(row.get("change_pct") or row.get("changePercent")),
                            "regime": "بيانات EGX30 الحالية متاحة",
                        }

        # EODHD treats indices as INDX instruments, not EGX equities.
        for candidate in index_candidates:
            history = self._get(
                f"eod/{candidate}",
                {"period": "d", "order": "d"},
                timeout=25,
            )
            if not history.get("success"):
                continue
            rows = history.get("data") or []
            if not isinstance(rows, list) or len(rows) < 30:
                continue
            frame = self._series(rows)
            if len(frame) < 30:
                continue
            close = frame["close"]
            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]
            ret20 = close.pct_change(20).iloc[-1] * 100
            if close.iloc[-1] > sma20 > sma50 and ret20 > 0:
                regime = "إيجابي"
            elif close.iloc[-1] < sma20 < sma50 and ret20 < 0:
                regime = "ضعيف"
            else:
                regime = "متذبذب"
            return {
                "success": True, "available": True, "symbol": candidate,
                "date": str(frame.iloc[-1]["date"].date()),
                "close": self._num(close.iloc[-1]),
                "sma20": self._num(sma20),
                "sma50": self._num(sma50),
                "return20": self._num(ret20),
                "regime": regime,
            }

        # Yahoo fallback for the Egyptian EGX30 benchmark.
        try:
            response = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5ECASE30",
                params={"range": "2y", "interval": "1d", "events": "history"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            item = ((payload.get("chart") or {}).get("result") or [None])[0]
            if item:
                ts = item.get("timestamp") or []
                q = ((item.get("indicators") or {}).get("quote") or [{}])[0]
                closes = q.get("close") or []
                rows = [
                    {"date": datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d"), "close": closes[i]}
                    for i, stamp in enumerate(ts)
                    if i < len(closes) and closes[i] is not None
                ]
                if len(rows) >= 30:
                    frame = self._series(rows)
                    close = frame["close"]
                    sma20 = close.rolling(20).mean().iloc[-1]
                    sma50 = close.rolling(50).mean().iloc[-1]
                    ret20 = close.pct_change(20).iloc[-1] * 100
                    if close.iloc[-1] > sma20 > sma50 and ret20 > 0:
                        regime = "إيجابي"
                    elif close.iloc[-1] < sma20 < sma50 and ret20 < 0:
                        regime = "ضعيف"
                    else:
                        regime = "متذبذب"
                    return {
                        "success": True, "available": True, "symbol": "^CASE30",
                        "date": str(frame.iloc[-1]["date"].date()),
                        "close": self._num(close.iloc[-1]),
                        "sma20": self._num(sma20),
                        "sma50": self._num(sma50),
                        "return20": self._num(ret20),
                        "regime": regime,
                    }
        except (requests.RequestException, ValueError, TypeError, KeyError):
            pass

        return {
            "success": True,
            "available": False,
            "symbol": "EGX30",
            "date": None,
            "close": None,
            "sma20": None,
            "sma50": None,
            "return20": None,
            "regime": "بيانات المؤشر غير متاحة",
            "message": "بيانات EGX30 غير متاحة حاليًا من مزودي الأسعار. تم الاستمرار بدون قراءة المؤشر.",
        }
        if not history["success"] or len(history["data"]) < 30:
            # Yahoo lists the EGX 30 benchmark as ^CASE30.
            try:
                response = requests.get(
                    "https://query1.finance.yahoo.com/v8/finance/chart/%5ECASE30",
                    params={"range": "2y", "interval": "1d", "events": "history"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )
                response.raise_for_status()
                payload = response.json()
                item = ((payload.get("chart") or {}).get("result") or [None])[0]
                if item:
                    ts = item.get("timestamp") or []
                    q = ((item.get("indicators") or {}).get("quote") or [{}])[0]
                    rows = []
                    for i, stamp in enumerate(ts):
                        closes = q.get("close") or []
                        if i < len(closes) and closes[i] is not None:
                            rows.append({"date": datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d"), "close": closes[i]})
                    rows.sort(key=lambda x: x["date"])
                    if len(rows) >= 30:
                        frame = self._series(rows)
                        close = frame["close"]
                        sma20 = close.rolling(20).mean().iloc[-1]
                        sma50 = close.rolling(50).mean().iloc[-1]
                        ret20 = close.pct_change(20).iloc[-1] * 100
                        if close.iloc[-1] > sma20 > sma50 and ret20 > 0:
                            regime = "إيجابي"
                        elif close.iloc[-1] < sma20 < sma50 and ret20 < 0:
                            regime = "ضعيف"
                        else:
                            regime = "متذبذب"
                        return {"success": True, "available": True, "symbol": "^CASE30",
                                "date": str(frame.iloc[-1]["date"].date()), "close": self._num(close.iloc[-1]),
                                "sma20": self._num(sma20), "sma50": self._num(sma50),
                                "return20": self._num(ret20), "regime": regime}
            except (requests.RequestException, ValueError, TypeError, KeyError):
                pass
            return {
                "success": True,
                "available": False,
                "symbol": self.normalize_symbol(index_symbol),
                "date": None,
                "close": None,
                "sma20": None,
                "sma50": None,
                "return20": None,
                "regime": "بيانات المؤشر غير متاحة",
                "message": "بيانات EGX30 غير متاحة حاليًا من مزود الأسعار. تم الاستمرار بدون قراءة المؤشر.",
            }
        frame = self._series(history["data"])
        close = frame["close"]
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        ret20 = close.pct_change(20).iloc[-1] * 100
        if close.iloc[-1] > sma20 > sma50 and ret20 > 0:
            regime = "إيجابي"
        elif close.iloc[-1] < sma20 < sma50 and ret20 < 0:
            regime = "ضعيف"
        else:
            regime = "متذبذب"
        return {"success": True, "symbol": history["symbol"], "date": str(frame.iloc[-1]["date"].date()), "close": self._num(close.iloc[-1]), "sma20": self._num(sma20), "sma50": self._num(sma50), "return20": self._num(ret20), "regime": regime}

    def _opportunity_setup(self, analysis, market=None, news_score=None):
        close, rsi, ret20 = analysis.get("close"), analysis.get("rsi14"), analysis.get("return20")
        atr, support = analysis.get("atr14"), analysis.get("support")
        volume_ratio = analysis.get("volume_ratio")
        rebound = 0.0
        if rsi is not None:
            if rsi <= 30: rebound += 28
            elif rsi <= 35: rebound += 22
            elif rsi <= 40: rebound += 14
            elif rsi <= 45: rebound += 6
        if ret20 is not None and ret20 < 0: rebound += min(20, abs(ret20) * 0.9)
        if close and support:
            distance = (close - support) / close * 100
            if distance <= 3: rebound += 18
            elif distance <= 6: rebound += 12
            elif distance <= 10: rebound += 6
        if volume_ratio is not None and volume_ratio >= 1.15: rebound += 10
        if analysis.get("change_pct") is not None and analysis["change_pct"] > 0: rebound += 8
        rebound = min(100, rebound)
        trend = float(analysis.get("opportunity_score") or 0)
        risk = float(analysis.get("risk_score") or 0)
        market_adj = 8 if market and market.get("regime") == "إيجابي" else (-10 if market and market.get("regime") == "ضعيف" else 0)
        news_adj = max(-8, min(8, news_score * 8)) if news_score is not None else 0
        ml_probability = analysis.get("ml", {}).get("probability") if isinstance(analysis.get("ml"), dict) and analysis.get("ml", {}).get("success") else None
        ml_adj = ((float(ml_probability) - 50.0) * 0.12) if ml_probability is not None else 0
        final_score = max(0, min(100, round(trend * 0.35 + rebound * 0.45 + (100-risk) * 0.20 + market_adj + news_adj + ml_adj)))
        setup = "ارتداد محتمل" if rebound >= 55 else ("تحت المراقبة" if rebound >= 35 else "لا توجد إشارة ارتداد كافية")
        target1 = close + atr if close is not None and atr else None
        target2 = close + (2 * atr) if close is not None and atr else None
        stop = close - (1.2 * atr) if close is not None and atr else None
        rr = ((target1-close)/(close-stop)) if target1 is not None and stop is not None and close != stop else None
        return {"rebound_score": round(rebound), "final_opportunity_score": final_score, "setup": setup, "entry_reference": close, "target1": target1, "target2": target2, "stop": stop, "invalidation": support * 0.98 if support else None, "risk_reward": rr, "market_regime": (market or {}).get("regime", "غير متاح"), "news_score": news_score, "ml_probability": ml_probability}

    @st.cache_data(ttl=900, show_spinner=False)
    def get_opportunities(_self, limit=20):
        import json
        filters = [["exchange", "=", _self.EGX_EXCHANGE], ["code", "in", SHARIA_SYMBOLS], ["refund_5d_p", "<", 0]]
        screen = _self._get("screener", {"filters": json.dumps(filters, ensure_ascii=False), "sort": "refund_5d_p.asc", "limit": 100}, timeout=40)
        candidates = (screen.get("data") or {}).get("data", []) if screen.get("success") else []
        if not candidates: candidates = [{"code": s} for s in SHARIA_SYMBOLS]
        market = _self.get_market_context()
        rows = []
        for item in candidates[:len(SHARIA_SYMBOLS)]:
            symbol = str(item.get("code") or "").upper()
            if symbol not in SHARIA_SYMBOLS: continue
            analysis = _self.analyze_stock(symbol)
            if not analysis.get("success"): continue
            news = _self.get_news(symbol, limit=5)
            news_rows = news.get("data", []) if news.get("success") else []
            polarities = [_self._num(x.get("polarity")) for x in news_rows]
            polarities = [x for x in polarities if x is not None]
            news_score = (sum(polarities) / len(polarities)) if polarities else None
            setup = _self._opportunity_setup(analysis, market, news_score)
            if setup["rebound_score"] < 30: continue
            rows.append({"symbol": symbol, "name": _self.arabic_company_name(symbol, item.get("name") or symbol),
                "name_en": item.get("name") or symbol, "date": analysis.get("date"), "close": analysis.get("close"), "change_pct": analysis.get("change_pct"), "rsi14": analysis.get("rsi14"), "return20": analysis.get("return20"), "volume_ratio": analysis.get("volume_ratio"), "support": analysis.get("support"), "resistance": analysis.get("resistance"), "risk_score": analysis.get("risk_score"), "opportunity_score": setup["final_opportunity_score"], **setup, "sharia_compliant": True, "sharia_source": REFERENCE_SOURCE, "sharia_reference_date": REFERENCE_DATE})
        rows.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return {"success": True, "data": rows[:max(1, min(int(limit), 40))], "count": len(rows), "market": market, "sharia_universe_count": len(SHARIA_SYMBOLS)}


    def get_premarket_report(self, limit=5):
        """Build the daily pre-market decision screen using the latest completed EGX session."""
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Africa/Cairo"))
        trading_day = now.weekday() in (6, 0, 1, 2, 3)
        market = self.get_market_context()
        if not market.get("success"):
            return {"success": False, "error": market.get("error", "تعذر قراءة حالة السوق")}
        opportunities = self.get_opportunities(limit=max(5, min(int(limit), 20)))
        if not opportunities.get("success"):
            return {"success": False, "error": opportunities.get("error", "تعذر فحص الفرص")}
        latest_session_date = market.get("date")
        if not latest_session_date:
            latest_session_date = next(
                (row.get("date") for row in opportunities.get("data", []) if row.get("date")),
                None,
            )
        latest_session_date = latest_session_date or "غير متاح من مزود البيانات"
        return {
            "success": True,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "trading_day": trading_day,
            "before_open": now.hour < 10,
            "market": market,
            "opportunities": opportunities.get("data", [])[:max(1, min(int(limit), 20))],
            "latest_session_date": latest_session_date,
            "sharia_universe_count": opportunities.get("sharia_universe_count", len(SHARIA_SYMBOLS)),
        }

    def get_full_analysis(self, symbol):
        technical = self.analyze_stock(symbol)
        if not technical.get("success"): return technical
        symbol_display = self.display_symbol(symbol)
        sharia = symbol_display in SHARIA_SYMBOLS
        fundamentals = self.get_company_snapshot(symbol_display)
        news = self.get_news(symbol_display, limit=8)
        news_rows = news.get("data", []) if news.get("success") else []
        vals = [x["polarity"] for x in news_rows if x.get("polarity") is not None]
        news_score = sum(vals) / len(vals) if vals else None
        market = self.get_market_context()
        setup = self._opportunity_setup(technical, market, news_score)
        return {**technical, "sharia_compliant": sharia, "sharia_source": REFERENCE_SOURCE, "sharia_reference_date": REFERENCE_DATE, "fundamentals": fundamentals if fundamentals.get("success") else {}, "news": news_rows, **setup}


data_engine = DataEngine()
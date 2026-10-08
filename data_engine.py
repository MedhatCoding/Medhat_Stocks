import os
import re
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st

from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE, REFERENCE_SOURCE
try:
    from sharia_funds import SHARIA_INDEX_FUNDS, SHARIA_FUND_MAP
except ImportError:
    # Keep Streamlit deploys resilient if an older checkout is still cached.
    SHARIA_INDEX_FUNDS = [
        {"symbol": "BWA", "name": "بلتون وفرة للاستثمار في أسهم مؤشر الشريعة EGX33", "type": "صندوق مؤشر", "benchmark": "EGX33 Shariah"},
        {"symbol": "CSF", "name": "مصر شريعة إكويتي - للاستثمار في مؤشر الشريعة EGX33", "type": "صندوق مؤشر", "benchmark": "EGX33 Shariah"},
    ]
    SHARIA_FUND_MAP = {x["symbol"]: x for x in SHARIA_INDEX_FUNDS}
try:
    from gold_funds import GOLD_FUNDS, GOLD_FUND_MAP
except ImportError:
    GOLD_FUNDS = []
    GOLD_FUND_MAP = {}
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
        except requests.RequestException:
            # Do not echo request URLs: they can contain the EODHD API token.
            return {"success": False, "error": "تعذر الاتصال بمزود بيانات الأسعار."}
        except ValueError:
            return {"success": False, "error": "استجابة غير صالحة من مزود البيانات."}

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
        result = self._oanor_get("egx-api/v1/quote", {"codes": code}, timeout=15)
        if not result["success"]:
            return result
        data = result["data"]
        rows = (data.get("quotes") or data.get("data")) if isinstance(data, dict) else data
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
        for fund in SHARIA_INDEX_FUNDS:
            code, name = fund["symbol"], fund["name"]
            q = query
            if q in code.upper() or q in name.upper():
                ranked.append((-1, code, name))
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
        # Arabic aliases are maintained locally so they remain searchable even
        # when the external symbol-list endpoint is unavailable.
        folded = query.casefold()
        for code, arabic_name in _self.ARABIC_COMPANY_NAMES.items():
            arabic_folded = arabic_name.casefold()
            if folded in arabic_folded or arabic_folded in folded:
                ranked.append((3, code, arabic_name))
        ranked.sort(key=lambda x: (x[0], x[1]))
        unique = []
        seen = set()
        for _, code, name in ranked:
            if code in seen:
                continue
            seen.add(code)
            unique.append({"symbol": code, "name": name})
            if len(unique) >= limit:
                break
        return unique

    def resolve_symbol(self, query):
        """Resolve a ticker, Arabic alias, or English company name to its ticker."""
        raw = (query or "").strip()
        if not raw:
            return ""
        code = self.display_symbol(raw)
        if code in SHARIA_SYMBOLS or code in SHARIA_FUND_MAP:
            return code
        if re.fullmatch(r"[A-Z0-9]{2,8}", raw.upper()):
            return code
        folded = raw.casefold()
        for symbol, arabic_name in self.ARABIC_COMPANY_NAMES.items():
            name = arabic_name.casefold()
            if folded in name or name in folded:
                return symbol
        matches = self.search_symbols(raw, limit=1)
        return matches[0]["symbol"] if matches else code

    def _yahoo_index_history(self, yahoo_symbols, period="2y"):
        """Yahoo fallback for EGX index tickers; indices use ^ tickers."""
        for yahoo_symbol in yahoo_symbols:
            try:
                response = requests.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                    params={"range": period, "interval": "1d", "events": "history"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )
                response.raise_for_status()
                payload = response.json()
                item = ((payload.get("chart") or {}).get("result") or [None])[0]
                if not item:
                    continue
                timestamps = item.get("timestamp") or []
                quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
                closes = quote.get("close") or []
                rows = []
                for i, ts in enumerate(timestamps):
                    if i >= len(closes) or closes[i] is None:
                        continue
                    rows.append({"date": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"), "close": closes[i]})
                if rows:
                    return {"success": True, "data": rows, "provider": "Yahoo Finance"}
            except (requests.RequestException, ValueError, TypeError, KeyError):
                continue
        return {"success": False, "data": []}

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
        """Return the freshest available EGX quote, preferring OANOR."""
        normalized = self.normalize_symbol(symbol)
        if not normalized:
            return {"success": False, "symbol": "", "price": None, "error": "رمز السهم غير صالح"}

        live = self.get_live_quote(normalized)
        if live.get("success"):
            row = live.get("data") or {}
            close = self._num(row.get("price") or row.get("close") or row.get("last"))
            previous = self._num(
                row.get("previous_close") or row.get("prev_close") or
                row.get("previousClose") or row.get("prevClose")
            )
            raw_change = row.get("change_percent")
            if raw_change is None:
                raw_change = row.get("change_pct")
            if raw_change is None:
                raw_change = row.get("changePercent")
            change_pct = self._num(raw_change)
            if close is not None:
                if change_pct is None and previous not in (None, 0):
                    change_pct = (close / previous - 1) * 100
                return {
                    "success": True, "symbol": normalized, "date": row.get("date") or row.get("timestamp"),
                    "open": row.get("open"), "high": row.get("high"), "low": row.get("low"),
                    "close": close, "price": close, "volume": row.get("volume"),
                    "previous_close": previous, "change_pct": change_pct, "provider": "OANOR",
                }

        result = self.get_stock_history(normalized, days=5)
        if not result.get("success") or not result.get("data"):
            return {"success": False, "symbol": normalized, "price": None,
                    "error": result.get("error", "لا توجد بيانات")}
        row = result["data"][0]
        previous = result["data"][1] if len(result["data"]) > 1 else {}
        close = self._num(row.get("close"))
        prev_close = self._num(previous.get("close"))
        change = close - prev_close if close is not None and prev_close is not None else None
        change_pct = (change / prev_close * 100) if change is not None and prev_close else None
        return {
            "success": True, "symbol": result["symbol"], "date": row.get("date"),
            "open": row.get("open"), "high": row.get("high"), "low": row.get("low"),
            "close": close, "price": close, "volume": row.get("volume"),
            "previous_close": prev_close, "change": change, "change_pct": change_pct,
            "provider": result.get("provider", "historical"),
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

    @st.cache_data(ttl=900, show_spinner=False)
    def analyze_stock(_self, symbol):
        history = _self.get_stock_history(symbol, days=500)
        if not history["success"] or not history["data"]:
            return {"success": False, "error": history.get("error", "لا توجد بيانات")}

        frame = _self._series(history["data"])
        if len(frame) < 80:
            return {"success": False, "error": "البيانات التاريخية المتاحة أقل من 80 جلسة"}

        close = frame["close"].astype(float)
        volume = frame["volume"].astype(float) if "volume" in frame else pd.Series(index=frame.index, dtype=float)
        frame["sma20"] = close.rolling(20).mean()
        frame["sma50"] = close.rolling(50).mean()
        frame["sma200"] = close.rolling(200).mean()
        ema12, ema26 = close.ewm(span=12, adjust=False).mean(), close.ewm(span=26, adjust=False).mean()
        frame["macd"] = ema12 - ema26
        frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
        frame["macd_hist"] = frame["macd"] - frame["macd_signal"]

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        frame["rsi14"] = 100 - (100 / (1 + rs))
        tr = pd.concat([
            frame["high"] - frame["low"],
            (frame["high"] - frame["close"].shift()).abs(),
            (frame["low"] - frame["close"].shift()).abs(),
        ], axis=1).max(axis=1)
        frame["atr14"] = tr.rolling(14).mean()
        frame["return_20d"] = close.pct_change(20) * 100
        frame["return_60d"] = close.pct_change(60) * 100
        frame["volatility20"] = close.pct_change().rolling(20).std() * np.sqrt(252) * 100
        frame["volume_avg20"] = volume.rolling(20).mean() if not volume.empty else np.nan
        frame["volume_ratio"] = volume / frame["volume_avg20"] if not volume.empty else np.nan

        latest = frame.iloc[-1]
        last_close = _self._num(latest["close"])
        sma20, sma50, sma200 = map(lambda k: _self._num(latest.get(k)), ["sma20","sma50","sma200"])
        rsi, atr = _self._num(latest.get("rsi14")), _self._num(latest.get("atr14"))
        ret20, ret60 = _self._num(latest.get("return_20d")), _self._num(latest.get("return_60d"))
        vol20, vol_ratio = _self._num(latest.get("volatility20")), _self._num(latest.get("volume_ratio"))
        macd, macd_signal, macd_hist = map(lambda k: _self._num(latest.get(k)), ["macd","macd_signal","macd_hist"])

        recent = frame.tail(60)
        support = _self._num(recent["low"].min())
        resistance = _self._num(recent["high"].max())
        atr_pct = (atr / last_close * 100) if atr and last_close else None

        # Multi-factor technical score.
        trend = 0
        for condition, points in [
            (last_close is not None and sma20 is not None and last_close > sma20, 12),
            (last_close is not None and sma50 is not None and last_close > sma50, 12),
            (sma20 is not None and sma50 is not None and sma20 > sma50, 12),
            (sma50 is not None and sma200 is not None and sma50 > sma200, 10),
            (ret20 is not None and ret20 > 0, 8),
            (ret60 is not None and ret60 > 0, 8),
            (macd_hist is not None and macd_hist > 0, 10),
            (rsi is not None and 45 <= rsi <= 68, 8),
        ]:
            trend += points
        momentum = 0
        if ret20 is not None: momentum += max(0, min(35, ret20 * 3))
        if ret60 is not None: momentum += max(0, min(35, ret60 * 1.5))
        if vol_ratio is not None and vol_ratio >= 1.15: momentum += 15
        if macd_hist is not None and macd_hist > 0: momentum += 15
        momentum = min(100, momentum)

        risk = 0
        if vol20 is not None: risk += min(35, max(0, vol20 - 12))
        if rsi is not None and rsi > 75: risk += 20
        if atr_pct is not None: risk += min(30, atr_pct * 3)
        if vol_ratio is not None and vol_ratio < 0.5: risk += 15
        risk_score = int(min(100, round(risk)))

        # Relative strength against the Sharia benchmark EGX33.
        rs20 = rs60 = None
        benchmark = _self.get_market_indices()
        egx33 = next((x for x in benchmark.get("indices", []) if x.get("symbol") == "EGX33"), None)
        if egx33:
            b20, b60 = _self._num(egx33.get("return20")), None
            # The board currently exposes 20-session benchmark performance; use
            # the stock's 60d return only as a secondary comparison when 60d
            # benchmark history is unavailable.
            if ret20 is not None and b20 is not None:
                rs20 = ret20 - b20
        relative_score = 50 if rs20 is None else max(0, min(100, 50 + rs20 * 5))

        # Fundamental quality, when available, is deliberately a bonus rather
        # than a hard requirement because some EGX names have incomplete data.
        fundamentals = _self.get_company_snapshot(symbol)
        fundamental_score = None
        if fundamentals.get("success"):
            f = fundamentals
            checks = []
            pe = _self._num(f.get("pe") or f.get("valuation_pe"))
            beta = _self._num(f.get("beta"))
            div = _self._num(f.get("dividend_yield"))
            if pe is not None: checks.append(70 if 0 < pe <= 18 else 45 if pe <= 30 else 25)
            if beta is not None: checks.append(70 if 0 < beta <= 1.2 else 45)
            if div is not None: checks.append(65 if div >= 2 else 50)
            if checks: fundamental_score = sum(checks) / len(checks)

        base_score = trend * 0.50 + momentum * 0.20 + relative_score * 0.15 + (fundamental_score or 50) * 0.15
        opportunity_score = int(max(0, min(100, round(base_score - risk_score * 0.25 + 8))))

        hard_blocks = []
        if vol_ratio is not None and vol_ratio < 0.35: hard_blocks.append("سيولة ضعيفة جدًا")
        if last_close is not None and sma50 is not None and last_close < sma50 and ret20 is not None and ret20 < -5:
            hard_blocks.append("اتجاه هابط قوي")
        if atr_pct is not None and atr_pct > 9: hard_blocks.append("تذبذب مرتفع جدًا")
        if last_close is not None and resistance and last_close >= resistance * 0.985:
            hard_blocks.append("السعر قريب جدًا من مقاومة")
        if rsi is not None and rsi >= 78: hard_blocks.append("تشبع شرائي")

        # Dynamic levels: volatility-adjusted, never fabricated when ATR is absent.
        entry_low = entry_high = target1 = target2 = stop = None
        if last_close is not None and atr and atr > 0:
            entry_low, entry_high = last_close - 0.35 * atr, last_close + 0.15 * atr
            target1, target2 = last_close + 1.0 * atr, last_close + 2.0 * atr
            stop = max(0.01, last_close - 1.25 * atr)

        if hard_blocks:
            status = "انتظار"
        elif opportunity_score >= 75 and risk_score < 50:
            status = "فرصة قوية"
        elif opportunity_score >= 60:
            status = "مراقبة"
        else:
            status = "محايد"

        ml = train_and_predict(frame, feedback=adaptive_feedback())
        ml_prob = _self._num((ml or {}).get("probability"))
        confidence = None
        if ml_prob is not None:
            confidence = round(max(0, min(100, 0.55 * opportunity_score + 0.45 * ml_prob)), 1)

        return {
            "success": True, "symbol": history["symbol"],
            "name": _self.arabic_company_name(symbol, symbol),
            "date": str(latest["date"].date()), "close": last_close,
            "open": _self._num(latest.get("open")), "high": _self._num(latest.get("high")),
            "low": _self._num(latest.get("low")), "volume": _self._num(latest.get("volume")),
            "previous_close": _self._num(frame.iloc[-2]["close"]) if len(frame)>1 else None,
            "change_pct": ((last_close / _self._num(frame.iloc[-2]["close"]) - 1)*100) if len(frame)>1 and _self._num(frame.iloc[-2]["close"]) else None,
            "sma20": sma20, "sma50": sma50, "sma200": sma200, "rsi14": rsi,
            "atr14": atr, "atr_pct": atr_pct, "macd": macd, "macd_signal": macd_signal,
            "macd_hist": macd_hist, "return20": ret20, "return60": ret60,
            "volatility20": vol20, "volume_ratio": vol_ratio, "support": support,
            "resistance": resistance,
            "distance_support_pct": ((last_close-support)/last_close*100) if last_close and support else None,
            "trend20": (last_close/sma20-1) if last_close and sma20 else None,
            "trend50": (last_close/sma50-1) if last_close and sma50 else None,
            "relative_strength_egx33": rs20, "relative_score": round(relative_score,1),
            "fundamental_score": round(fundamental_score,1) if fundamental_score is not None else None,
            "opportunity_score": opportunity_score, "final_opportunity_score": opportunity_score,
            "risk_score": risk_score, "confidence": confidence, "hard_blocks": hard_blocks,
            "status": status, "history_rows": len(frame),
            "entry_low": entry_low, "entry_high": entry_high, "target1": target1,
            "target2": target2, "stop": stop,
            "chart": frame.tail(120)[["date","close","sma20","sma50","sma200"]].assign(
                date=lambda x: x["date"].dt.strftime("%Y-%m-%d")),
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
        except requests.RequestException:
            # Gemini API keys are sent as query parameters; never echo request URLs.
            return {"success": False, "error": "تعذر الاتصال بمحرك AI."}
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
                row = (payload.get("data") or payload.get("index") or payload.get("indices")) if isinstance(payload, dict) else payload
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
                            "change_pct": self._num(row.get("change_percent") or row.get("change_pct") or row.get("changePercent")),
                            "return20": None,
                            "regime": "بيانات EGX30 الحالية متاحة", "provider": "OANOR",
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

    @st.cache_data(ttl=600, show_spinner=False)
    def get_market_indices(_self):
        """Return the main EGX indices, with EGX33/Shariah treated as first-class."""
        specs = [
            {"name":"EGX30","symbol":"EGX30","candidates":["EGX30.INDX","CASE30.INDX","CASE30"],"yahoo":["%5ECASE30"]},
            {"name":"EGX33 Shariah","symbol":"EGX33","candidates":["EGX33.INDX","EGX33"],"yahoo":["%5EEGX33.CA","%5EEGX33"]},
            {"name":"EGX35-LV","symbol":"EGX35-LV","candidates":["EGX35LV.INDX","EGX35-LV.INDX","EGX35LV"],"yahoo":["%5EEGX35LV.CA","%5EEGX35LV"]},
            {"name":"EGX70 EWI","symbol":"EGX70EWI","candidates":["EGX70EWI.INDX","EGX70.INDX","CCSI.INDX"],"yahoo":["%5EEGX70EWI.CA","%5EEGX70EWI","%5EEGX70"]},
            {"name":"EGX100 EWI","symbol":"EGX100EWI","candidates":["EGX100EWI.INDX","EGX100.INDX","EGX100"],"yahoo":["%5EEGX100EWI.CA","%5EEGX100EWI","%5EEGX100"]},
            {"name":"EGX30 Capped","symbol":"EGX30CAP","candidates":["EGX30CAP.INDX","EGX30CAP"],"yahoo":["%5EEGX30CAP.CA","%5EEGX30CAP"]},
            {"name":"EGX30-TR","symbol":"EGX30TR","candidates":["EGX30TR.INDX","EGX30TR"],"yahoo":["%5EEGX30TR.CA","%5EEGX30TR"]},
            {"name":"TAMAYUZ","symbol":"TAMAYUZ","candidates":["TAMAYUZ.INDX","TAMAYUZ"],"yahoo":["%5ETAMAYUZ.CA","%5ETAMAYUZ"]},
        ]

        def calc(rows):
            if not isinstance(rows, list):
                return None
            frame = _self._series(rows)
            if len(frame) < 2 or "close" not in frame:
                return None
            close = frame["close"].dropna()
            if len(close) < 2:
                return None
            last = _self._num(close.iloc[-1])
            prev = _self._num(close.iloc[-2])
            if last is None:
                return None
            change_pct = ((last / prev) - 1) * 100 if prev not in (None, 0) else None
            ret20 = ((last / close.iloc[-21]) - 1) * 100 if len(close) >= 21 else None
            sma20 = close.tail(20).mean() if len(close) >= 20 else None
            sma50 = close.tail(50).mean() if len(close) >= 50 else None
            if sma20 is not None and sma50 is not None and last > sma20 > sma50 and (ret20 or 0) > 0:
                regime = "إيجابي"
            elif sma20 is not None and sma50 is not None and last < sma20 < sma50 and (ret20 or 0) < 0:
                regime = "ضعيف"
            else:
                regime = "متذبذب"
            date_value = frame.iloc[-1].get("date")
            return {
                "close": last,
                "change_pct": change_pct,
                "return20": ret20,
                "sma20": _self._num(sma20),
                "sma50": _self._num(sma50),
                "date": str(date_value.date()) if hasattr(date_value, "date") else str(date_value or ""),
                "regime": regime,
            }

        indices = []
        for spec in specs:
            item = None

            # EGX/OANOR currently exposes a dedicated index endpoint for EGX30.
            if spec["symbol"] == "EGX30" and _self.oanor_api_key:
                live = _self._oanor_get("egx-api/v1/index", timeout=15)
                if live.get("success"):
                    payload = live.get("data") or {}
                    row = payload.get("data") or payload.get("index") or payload
                    if isinstance(row, list):
                        row = row[0] if row else {}
                    if isinstance(row, dict):
                        value = _self._num(row.get("value") or row.get("close") or row.get("price"))
                        if value is not None:
                            item = {
                                "close": value,
                                "change_pct": _self._num(
                                    row.get("change_percent") if row.get("change_percent") is not None
                                    else row.get("change_pct") if row.get("change_pct") is not None
                                    else row.get("changePercent")
                                ),
                                "return20": None,
                                "sma20": None, "sma50": None,
                                "date": row.get("date") or row.get("timestamp") or "",
                                "regime": "متاح لحظيًا",
                            }

            # EODHD is the primary historical index source. Try only known symbols.
            if item is None:
                for candidate in spec["candidates"]:
                    history = _self._get(
                        f"eod/{candidate}",
                        {"period":"d","order":"d"},
                        timeout=20,
                    )
                    if history.get("success") and isinstance(history.get("data"), list):
                        item = calc(history["data"])
                        if item:
                            item["provider"] = "EODHD"
                            break

            # Yahoo is a last-resort historical source for verified index tickers.
            if item is None:
                y = _self._yahoo_index_history(spec.get("yahoo", []), period="2y")
                if y.get("success"):
                    item = calc(y.get("data", []))
                    if item:
                        item["provider"] = "Yahoo Finance"

            if item:
                indices.append({
                    "name": spec["name"],
                    "symbol": spec["symbol"],
                    **item,
                })

        # Keep the order fixed so EGX33 is always visible immediately after EGX30.
        return {
            "success": bool(indices),
            "count": len(indices),
            "expected_count": len(specs),
            "indices": indices,
            "missing": [x["name"] for x in specs if x["name"] not in {i["name"] for i in indices}],
        }

    @st.cache_data(ttl=300, show_spinner=False)
    def get_market_snapshot(_self, limit=96):
        """Build the Sharia EGX market board from OANOR live quotes in batches."""
        symbols = list(dict.fromkeys(SHARIA_SYMBOLS))[:max(1, int(limit))]
        allowed = set(_self.display_symbol(s) for s in symbols)
        rows = []

        if _self.oanor_api_key:
            for i in range(0, len(symbols), 20):
                batch = symbols[i:i + 20]
                result = _self._oanor_get(
                    "egx-api/v1/quote",
                    {"codes": ",".join(_self.display_symbol(s) for s in batch)},
                    timeout=20,
                )
                if not result.get("success"):
                    continue
                payload = result.get("data") or {}
                quotes = payload.get("quotes") if isinstance(payload, dict) else payload
                if not isinstance(quotes, list):
                    continue
                for q in quotes:
                    if not isinstance(q, dict):
                        continue
                    symbol = str(q.get("ticker") or q.get("code") or "").upper()
                    if symbol not in allowed:
                        continue
                    price = _self._num(q.get("price") or q.get("close"))
                    raw_change = q.get("change_percent")
                    if raw_change is None:
                        raw_change = q.get("changePercent")
                    change_pct = _self._num(raw_change)
                    volume = _self._num(q.get("volume"))
                    if price is None or change_pct is None:
                        continue
                    rows.append({
                        "symbol": symbol,
                        "name": _self.arabic_company_name(symbol, q.get("company") or symbol),
                        "name_en": q.get("company") or symbol,
                        "close": price,
                        "change_pct": change_pct,
                        "volume": volume,
                        "volume_ratio": None,
                        "provider": "OANOR",
                    })

        if not rows:
            for symbol in symbols:
                try:
                    hist = _self.get_stock_history(symbol, days=35)
                    data = hist.get("data", []) if hist.get("success") else []
                    if len(data) < 2:
                        continue
                    frame = _self._series(data)
                    if len(frame) < 2:
                        continue
                    last, prev = frame.iloc[-1], frame.iloc[-2]
                    close = _self._num(last.get("close"))
                    previous = _self._num(prev.get("close"))
                    volume = _self._num(last.get("volume"))
                    if close is None or previous in (None, 0):
                        continue
                    change = (close / previous - 1) * 100
                    avg_vol = frame["volume"].tail(20).mean() if "volume" in frame else None
                    volume_ratio = (volume / avg_vol) if volume is not None and avg_vol and avg_vol > 0 else None
                    rows.append({
                        "symbol": symbol,
                        "name": _self.arabic_company_name(symbol, symbol),
                        "close": close,
                        "change_pct": change,
                        "volume": volume,
                        "volume_ratio": volume_ratio,
                        "provider": hist.get("provider", "EODHD"),
                    })
                except Exception:
                    continue

        rows.sort(key=lambda x: x["change_pct"], reverse=True)
        gainers = rows[:5]
        losers = sorted(rows, key=lambda x: x["change_pct"])[:5]
        volume_leaders = sorted(rows, key=lambda x: x.get("volume") or 0, reverse=True)[:5]
        advances = sum(1 for x in rows if x["change_pct"] > 0.05)
        declines = sum(1 for x in rows if x["change_pct"] < -0.05)
        unchanged = len(rows) - advances - declines
        return {
            "success": bool(rows), "count": len(rows), "rows": rows,
            "gainers": gainers, "losers": losers, "volume_leaders": volume_leaders,
            "advances": advances, "declines": declines, "unchanged": unchanged,
            "breadth": round(advances / len(rows) * 100, 1) if rows else None,
            "provider": rows[0].get("provider") if rows else None,
        }

    def _opportunity_setup(self, analysis, market=None, news_score=None, seasonality_score=50):
        close = analysis.get("close")
        rsi = analysis.get("rsi14")
        ret20 = analysis.get("return20")
        atr = analysis.get("atr14")
        support = analysis.get("support")
        volume_ratio = analysis.get("volume_ratio")
        risk = float(analysis.get("risk_score") or 0)
        base = float(analysis.get("opportunity_score") or 0)
        hard_blocks = list(analysis.get("hard_blocks") or [])

        rebound = 0.0
        if rsi is not None:
            if rsi <= 30: rebound += 30
            elif rsi <= 35: rebound += 24
            elif rsi <= 40: rebound += 16
            elif rsi <= 45: rebound += 8
        if ret20 is not None and ret20 < 0:
            rebound += min(20, abs(ret20) * 0.9)
        if close and support:
            distance = (close - support) / close * 100
            if distance <= 3: rebound += 18
            elif distance <= 6: rebound += 12
            elif distance <= 10: rebound += 6
        if volume_ratio is not None and volume_ratio >= 1.15: rebound += 10
        if analysis.get("change_pct") is not None and analysis["change_pct"] > 0: rebound += 8
        rebound = min(100, rebound)

        regime = (market or {}).get("regime", "")
        market_adj = 7 if regime == "إيجابي" else (-10 if regime == "ضعيف" else 0)
        season_adj = max(-6, min(6, (float(seasonality_score) - 50) * 0.12))
        news_adj = max(-8, min(8, news_score * 8)) if news_score is not None else 0
        ml_data = analysis.get("ml", {}) if isinstance(analysis.get("ml"), dict) else {}
        ml_probability = ml_data.get("probability") if ml_data.get("success") else None
        ml_adj = ((float(ml_probability) - 50.0) * 0.12) if ml_probability is not None else 0
        relative = float(analysis.get("relative_score") or 50)
        final_score = max(0, min(100, round(
            base * 0.45 + rebound * 0.20 + (100-risk) * 0.15 +
            relative * 0.10 + 50 * 0.10 + market_adj + news_adj + ml_adj + season_adj
        )))
        if hard_blocks:
            final_score = min(final_score, 54)

        validation = ml_data.get("validation_accuracy")
        confidence_parts = [float(final_score)]
        if validation is not None: confidence_parts.append(float(validation))
        if analysis.get("confidence") is not None: confidence_parts.append(float(analysis["confidence"]))
        if ml_probability is not None: confidence_parts.append(100 - abs(float(ml_probability)-50) * 1.4)
        confidence_score = round(sum(confidence_parts) / len(confidence_parts))

        setup_label = "ارتداد محتمل" if rebound >= 55 else ("تحت المراقبة" if rebound >= 35 else "لا توجد إشارة ارتداد كافية")
        entry = close
        entry_low = analysis.get("entry_low")
        entry_high = analysis.get("entry_high")
        target1 = analysis.get("target1")
        target2 = analysis.get("target2")
        stop = analysis.get("stop")
        rr = ((target1-entry)/(entry-stop)) if target1 is not None and stop is not None and entry and entry != stop else None

        return {
            "rebound_score": round(rebound),
            "final_opportunity_score": final_score,
            "setup": setup_label,
            "entry_reference": entry,
            "entry_low": entry_low, "entry_high": entry_high,
            "target1": target1, "target2": target2, "stop": stop,
            "invalidation": support * 0.98 if support else None,
            "risk_reward": rr,
            "confidence_score": confidence_score,
            "confidence": analysis.get("confidence"),
            "ml_validation_accuracy": validation,
            "market_regime": regime or "غير متاح",
            "news_score": news_score,
            "ml_probability": ml_probability,
            "relative_strength_egx33": analysis.get("relative_strength_egx33"),
            "relative_score": analysis.get("relative_score"),
            "seasonality_score": round(float(seasonality_score), 1),
            "hard_blocks": hard_blocks,
            "defensive_bias": "ذهب/سيولة دفاعية" if (regime == "ضعيف" or float(seasonality_score) < 42) else "أسهم شرعية انتقائية",
        }

    @st.cache_data(ttl=900, show_spinner=False)
    def get_opportunities(_self, limit=20):
        import json
        filters = [["exchange", "=", _self.EGX_EXCHANGE], ["code", "in", SHARIA_SYMBOLS], ["refund_5d_p", "<", 0]]
        screen = _self._get("screener", {"filters": json.dumps(filters, ensure_ascii=False), "sort": "refund_5d_p.asc", "limit": 100}, timeout=40)
        candidates = (screen.get("data") or {}).get("data", []) if screen.get("success") else []
        if not candidates:
            # Protect API quotas if Screener is unavailable.
            candidates = [{"code": s} for s in SHARIA_SYMBOLS[:20]]
        # Close older recommendations first so the next ML run can learn from real outcomes.
        try:
            from recommendation_journal import evaluate_open
            evaluate_open(_self.get_stock_history, horizon=10)
        except Exception:
            pass
        market = _self.get_market_context()
        market_seasonality = _self.get_market_seasonality(min_years=3)
        seasonality_score = float(market_seasonality.get("score",50))
        rows = []
        for item in candidates[:20]:
            symbol = str(item.get("code") or "").upper()
            if symbol not in SHARIA_SYMBOLS: continue
            analysis = _self.analyze_stock(symbol)
            if not analysis.get("success"): continue
            news = _self.get_news(symbol, limit=5)
            news_rows = news.get("data", []) if news.get("success") else []
            polarities = [_self._num(x.get("polarity")) for x in news_rows]
            polarities = [x for x in polarities if x is not None]
            news_score = (sum(polarities) / len(polarities)) if polarities else None
            setup = _self._opportunity_setup(analysis, market, news_score, seasonality_score)
            # Keep the opportunities screen limited to qualified setups; do not
            # display blocked or high-risk candidates as actionable opportunities.
            if setup["hard_blocks"]:
                continue
            if setup["final_opportunity_score"] < 55:
                continue
            if setup["rebound_score"] < 45:
                continue
            if float(analysis.get("risk_score") or 100) > 65:
                continue
            rows.append({"symbol": symbol, "name": _self.arabic_company_name(symbol, item.get("name") or symbol),
                "name_en": item.get("name") or symbol, "date": analysis.get("date"), "close": analysis.get("close"), "change_pct": analysis.get("change_pct"), "rsi14": analysis.get("rsi14"), "return20": analysis.get("return20"), "volume_ratio": analysis.get("volume_ratio"), "support": analysis.get("support"), "resistance": analysis.get("resistance"), "risk_score": analysis.get("risk_score"), "opportunity_score": setup["final_opportunity_score"], **setup, "sharia_compliant": True, "sharia_source": REFERENCE_SOURCE, "sharia_reference_date": REFERENCE_DATE, "seasonality_score": setup.get("seasonality_score"), "defensive_bias": setup.get("defensive_bias")})
        rows.sort(key=lambda x: x["opportunity_score"], reverse=True)
        for row in rows[:max(1, min(int(limit), 40))]:
            try:
                record_opportunity(row)
            except Exception:
                pass
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

    def get_seasonality(self, frame, min_years=3):
        """Estimate calendar-month behavior without using the current month."""
        if frame is None or len(frame) < 180:
            return {"score": 50, "month": None, "avg_return": None, "samples": 0, "label": "بيانات موسمية غير كافية"}
        df = frame.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"]).sort_values("date")
        daily = df.set_index("date")["close"].resample("ME").last().pct_change() * 100
        if daily.empty:
            return {"score": 50, "month": None, "avg_return": None, "samples": 0, "label": "بيانات موسمية غير كافية"}
        current_month = datetime.now().month
        hist = daily[daily.index.month == current_month]
        if len(hist) < min_years:
            return {"score": 50, "month": current_month, "avg_return": None, "samples": int(len(hist)), "label": "بيانات موسمية غير كافية"}
        avg = float(hist.mean())
        positive = float((hist > 0).mean() * 100)
        score = max(0, min(100, 50 + avg * 4 + (positive - 50) * 0.35))
        label = "موسم قوي" if score >= 60 else ("موسم ضعيف" if score <= 40 else "موسم متوازن")
        return {"score": round(score, 1), "month": current_month, "avg_return": round(avg, 2), "samples": int(len(hist)), "positive_months_pct": round(positive, 1), "label": label}

    @st.cache_data(ttl=86400, show_spinner=False)
    def get_market_seasonality(_self, min_years=3):
        """Calendar-month behavior of the broad EGX30 market."""
        for candidate in ["EGX30.INDX", "CASE30.INDX"]:
            try:
                history = _self._get(f"eod/{candidate}", {"period": "d", "order": "d"}, timeout=25)
                rows = history.get("data") or [] if history.get("success") else []
                if len(rows) < 180:
                    continue
                frame = _self._series(rows)
                return _self.get_seasonality(frame, min_years=min_years)
            except Exception:
                continue
        return {"score": 50, "month": datetime.now().month, "avg_return": None, "samples": 0, "label": "بيانات موسمية للسوق غير كافية"}

    def get_gold_funds(self):
        return {"success":True,"funds":GOLD_FUNDS,"count":len(GOLD_FUNDS)}

    def get_asset_allocation_context(self):
        market = self.get_market_context()
        season = self.get_market_seasonality(min_years=3)
        return {
            "market": market,
            "market_regime": market.get("regime", "غير متاح"),
            "seasonality": season,
            "seasonality_score": season.get("score"),
            "sharia_funds": SHARIA_INDEX_FUNDS,
            "gold_funds": GOLD_FUNDS,
        }

    def get_full_analysis(self, symbol):
        technical = self.analyze_stock(symbol)
        if not technical.get("success"): return technical
        symbol_display = self.display_symbol(symbol)
        fund_info = SHARIA_FUND_MAP.get(symbol_display.upper())
        sharia = symbol_display in SHARIA_SYMBOLS or bool(fund_info)
        fundamentals = self.get_company_snapshot(symbol_display)
        news = self.get_news(symbol_display, limit=8)
        news_rows = news.get("data", []) if news.get("success") else []
        vals = [self._num(x.get("polarity")) for x in news_rows]
        vals = [value for value in vals if value is not None]
        news_score = sum(vals) / len(vals) if vals else None
        market = self.get_market_context()
        stock_history = self.get_stock_history(symbol, days=1825)
        stock_seasonality = self.get_seasonality(self._series(stock_history.get("data", [])), min_years=2)
        market_seasonality = self.get_market_seasonality(min_years=3)
        # Market seasonality is dominant; stock seasonality is secondary.
        seasonality_score = round(market_seasonality["score"] * 0.70 + stock_seasonality["score"] * 0.30, 1)
        seasonality = {**market_seasonality, "score": seasonality_score,
                       "market_score": market_seasonality["score"],
                       "stock_score": stock_seasonality["score"]}
        setup = self._opportunity_setup(technical, market, news_score)
        # Seasonality is a bounded modifier, never the primary signal.
        setup["seasonality_score"] = seasonality_score
        setup["seasonality"] = seasonality
        setup["final_opportunity_score"] = max(0, min(100, round(float(setup.get("final_opportunity_score", setup.get("opportunity_score", 50))) + (seasonality_score - 50) * 0.12)))
        return {**technical, "sharia_compliant": sharia, "sharia_fund": bool(fund_info), "fund_info": fund_info or {},
                "gold_funds": GOLD_FUNDS, "asset_allocation": self.get_asset_allocation_context(), "sharia_source": REFERENCE_SOURCE, "sharia_reference_date": REFERENCE_DATE, "fundamentals": fundamentals if fundamentals.get("success") else {}, "news": news_rows, **setup}


data_engine = DataEngine()
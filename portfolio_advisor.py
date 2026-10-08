"""Portfolio decision engine for Medhat_Stocks.

Produces one of three actions for an existing holding:
زيادة / احتفاظ / بيع.
It combines quantitative analysis, ML/DL probability, market regime,
seasonality, risk and current portfolio weight. It never invents prices.
"""
from data_engine import data_engine
from sharia_funds import SHARIAH_FUND_MAP
from gold_funds import GOLD_FUND_MAP
from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE

FUND_MAP = {**SHARIAH_FUND_MAP, **GOLD_FUND_MAP}


def _num(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def asset_info(symbol):
    s = str(symbol or "").upper().replace(".EGX", "")
    if s in FUND_MAP:
        item = FUND_MAP[s].copy()
        item["asset_type"] = item.get("type", "صندوق")
        return item
    return {"symbol": s, "name": data_engine.arabic_company_name(s, s),
            "asset_type": "سهم شرعي"}


def advise(position, analysis=None, market=None, portfolio_value=0.0):
    symbol = str(position.get("symbol") or "").upper().replace(".EGX", "")
    qty = _num(position.get("qty")) or 0
    avg = _num(position.get("avg")) or 0
    info = asset_info(symbol)

    # Never issue an add/hold/sell quantitative recommendation for an EGX stock
    # outside the configured Sharia reference universe.
    if info.get("asset_type") == "سهم شرعي" and symbol not in SHARIA_SYMBOLS:
        return {
            "action": "مراجعة شرعية", "action_key": "insufficient",
            "reason": f"السهم غير موجود في القائمة الشرعية المرجعية بتاريخ {REFERENCE_DATE}؛ لن يتم إصدار توصية كمية له.",
            "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
            "price": None, "pnl_pct": None, "score": None, "risk": None,
        }

    if analysis is None:
        analysis = data_engine.analyze_stock(symbol)

    if info.get("asset_type") in ("صندوق مؤشر", "صندوق ذهب"):
        quote = data_engine.get_latest_price(symbol)
        price = _num(quote.get("close")) if quote.get("success") else None
        pnl_pct = ((price / avg) - 1) * 100 if price is not None and avg > 0 else None
        if not quote.get("success"):
            return {
                "action": "بيانات غير كافية", "action_key": "insufficient",
                "reason": "تعذر جلب السعر الحالي للصندوق؛ لن يتم اختلاق توصية.",
                "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
                "price": None, "pnl_pct": pnl_pct, "score": None, "risk": None,
            }
        regime = (market or {}).get("regime", "")
        if info.get("asset_type") == "صندوق مؤشر" and regime == "إيجابي":
            action, key, reason = "زيادة", "increase", "الصندوق يتتبع EGX33 الشريعة وحالة السوق العامة إيجابية."
        elif info.get("asset_type") == "صندوق مؤشر" and regime == "ضعيف":
            action, key, reason = "احتفاظ", "hold", "حالة السوق ضعيفة؛ لا توجد أفضلية لزيادة التعرض الآن."
        elif info.get("asset_type") == "صندوق مؤشر":
            action, key, reason = "احتفاظ", "hold", "حالة السوق متذبذبة؛ الاحتفاظ أفضل من مطاردة الحركة."
        else:
            action, key, reason = "احتفاظ", "hold", "الصندوق دفاعي، ولا توجد إشارة سعرية موثوقة كافية للبيع أو الزيادة."
        return {
            "action": action, "action_key": key, "reason": reason,
            "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
            "price": price, "pnl_pct": pnl_pct, "score": None, "risk": None,
            "ml_probability": None, "weight_pct": ((price * qty) / portfolio_value * 100) if portfolio_value and price is not None else 0.0,
        }

    if not analysis or not analysis.get("success"):
        return {
            "action": "بيانات غير كافية", "action_key": "insufficient",
            "reason": analysis.get("error", "لا توجد بيانات تحليلية كافية.") if isinstance(analysis, dict) else "لا توجد بيانات تحليلية كافية.",
            "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
            "price": None, "pnl_pct": None, "score": None, "risk": None,
        }

    price = _num(analysis.get("close"))
    pnl_pct = ((price / avg) - 1) * 100 if price is not None and avg > 0 else None
    score = _num(analysis.get("final_opportunity_score"))
    if score is None:
        score = _num(analysis.get("opportunity_score"))
    risk = _num(analysis.get("risk_score"))
    ml = analysis.get("ml") or {}
    ml_prob = _num(ml.get("probability"))
    deep_prob = _num(ml.get("deep_learning_probability"))
    ml_prob = 50.0 if ml_prob is None else ml_prob
    deep_prob = ml_prob if deep_prob is None else deep_prob
    if ml_prob > 1: ml_prob /= 100.0
    if deep_prob > 1: deep_prob /= 100.0
    combined_prob = (ml_prob + deep_prob) / 2

    regime = (market or {}).get("regime", "")
    seasonality = _num((market or {}).get("seasonality_score"))
    weight = 0.0
    if portfolio_value and price is not None:
        weight = (price * qty) / portfolio_value * 100

    decision_score = (score or 50) * 0.50 + combined_prob * 100 * 0.30 + (100 - (risk or 50)) * 0.20
    if "ضعيف" in regime:
        decision_score -= 7
    elif "إيجابي" in regime:
        decision_score += 4
    if seasonality is not None:
        if seasonality < 42:
            decision_score -= 5
        elif seasonality >= 60:
            decision_score += 3

    reasons = []
    if risk is not None and risk >= 70:
        reasons.append("المخاطر مرتفعة")
    if combined_prob >= 0.62:
        reasons.append("احتمال النمو من ML/DL جيد")
    elif combined_prob < 0.42:
        reasons.append("إشارة ML/DL ضعيفة")
    if score is not None and score >= 70:
        reasons.append("التقييم الكمي إيجابي")
    elif score is not None and score < 50:
        reasons.append("التقييم الكمي ضعيف")
    if "ضعيف" in regime:
        reasons.append("حالة السوق العامة ضعيفة")
    if weight >= 30:
        reasons.append("وزن المركز كبير نسبيًا")

    hard_blocks = analysis.get("hard_blocks") or []
    confidence = _num(analysis.get("confidence"))
    # Risk controls override bullish scores.
    if risk is not None and risk >= 82:
        action, key = "بيع", "sell"
    elif hard_blocks and ("اتجاه هابط قوي" in hard_blocks or "سيولة ضعيفة جدًا" in hard_blocks):
        action, key = "بيع", "sell"
    elif hard_blocks:
        action, key = "احتفاظ", "hold"
    elif decision_score >= 72 and combined_prob >= 0.62 and (confidence is None or confidence >= 68) and (risk is None or risk < 55) and weight < 25:
        action, key = "زيادة", "increase"
    elif decision_score < 42 or (combined_prob < 0.35 and risk is not None and risk >= 60):
        action, key = "بيع", "sell"
    else:
        action, key = "احتفاظ", "hold"

    if hard_blocks:
        reasons.append("فلتر أمان: " + "، ".join(hard_blocks[:2]))
    if not reasons:
        reasons.append("الإشارات الحالية متوازنة")

    return {
        "action": action, "action_key": key, "reason": " • ".join(reasons[:3]),
        "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
        "price": price, "pnl_pct": pnl_pct, "score": round(decision_score, 1),
        "risk": risk, "ml_probability": combined_prob, "confidence": confidence, "weight_pct": weight, "hard_blocks": hard_blocks,
    }

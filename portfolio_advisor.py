"""Portfolio decision engine for Medhat_Stocks.

Produces one of three actions for an existing holding:
زيادة / احتفاظ / بيع.
It combines quantitative analysis, ML/DL probability, market regime,
seasonality, risk and current portfolio weight. It never invents prices.
"""
from data_engine import data_engine
from sharia_funds import SHARIAH_FUND_MAP
from gold_funds import GOLD_FUND_MAP

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

    if analysis is None:
        analysis = data_engine.analyze_stock(symbol)

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
    combined_prob = ((ml_prob if ml_prob is not None else 0.5) + (deep_prob if deep_prob is not None else (ml_prob if ml_prob is not None else 0.5))) / 2

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

    if risk is not None and risk >= 78:
        action, key = "بيع", "sell"
    elif decision_score >= 70 and combined_prob >= 0.60 and (risk is None or risk < 55) and weight < 30:
        action, key = "زيادة", "increase"
    elif decision_score < 43 or (combined_prob < 0.35 and risk is not None and risk >= 60):
        action, key = "بيع", "sell"
    else:
        action, key = "احتفاظ", "hold"

    if not reasons:
        reasons.append("الإشارات الحالية متوازنة")

    return {
        "action": action, "action_key": key, "reason": " • ".join(reasons[:3]),
        "symbol": symbol, "name": info["name"], "asset_type": info["asset_type"],
        "price": price, "pnl_pct": pnl_pct, "score": round(decision_score, 1),
        "risk": risk, "ml_probability": combined_prob, "weight_pct": weight,
    }

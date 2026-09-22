import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

JOURNAL_FILE = os.getenv("RECOMMENDATION_JOURNAL_FILE", "recommendation_journal.json")


def _read():
    try:
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _write(rows):
    directory = os.path.dirname(JOURNAL_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = JOURNAL_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    os.replace(tmp, JOURNAL_FILE)


def record_opportunity(row):
    symbol = str(row.get("symbol") or "").upper()
    date = str(row.get("date") or "")
    if not symbol:
        return False
    rows = _read()
    key = f"{date}|{symbol}|{row.get('entry_reference')}"
    if any(x.get("key") == key for x in rows):
        return False
    rows.append({
        "key": key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "name": row.get("name"),
        "date": date,
        "entry": row.get("entry_reference"),
        "target1": row.get("target1"),
        "target2": row.get("target2"),
        "stop": row.get("stop"),
        "score": row.get("opportunity_score"),
        "risk_score": row.get("risk_score"),
        "rebound_score": row.get("rebound_score"),
        "ml_probability": row.get("ml_probability"),
        "market_regime": row.get("market_regime"),
        "features": {
            "rsi14": row.get("rsi14"), "return20": row.get("return20"),
            "return60": row.get("return60"), "volatility20": row.get("volatility20"),
            "volume_ratio": row.get("volume_ratio"), "atr_pct": row.get("atr_pct"),
            "distance_support_pct": row.get("distance_support_pct"),
            "trend20": row.get("trend20"), "trend50": row.get("trend50"),
        },
        "status": "open",
        "outcome": None,
        "outcome_return_pct": None,
        "closed_at": None,
    })
    _write(rows)
    return True


def evaluate_open(history_loader, horizon=10):
    rows = _read()
    changed = 0
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if row.get("status") != "open":
            continue
        history = history_loader(row["symbol"], days=max(30, horizon + 5))
        data = history.get("data", []) if history.get("success") else []
        if not data:
            continue
        frame = pd.DataFrame(data)
        if "date" not in frame or "close" not in frame:
            continue
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["high"] = pd.to_numeric(frame.get("high"), errors="coerce")
        frame["low"] = pd.to_numeric(frame.get("low"), errors="coerce")
        frame = frame.dropna(subset=["date", "close"]).sort_values("date")
        start = pd.to_datetime(row.get("date"), errors="coerce")
        if pd.isna(start):
            continue
        future = frame[frame["date"] > start].head(horizon)
        if len(future) < horizon:
            continue
        entry = float(row.get("entry") or 0)
        target1 = float(row.get("target1") or 0)
        target2 = float(row.get("target2") or 0)
        stop = float(row.get("stop") or 0)
        hit_t2 = bool((future["high"] >= target2).any()) if target2 else False
        hit_t1 = bool((future["high"] >= target1).any()) if target1 else False
        hit_stop = bool((future["low"] <= stop).any()) if stop else False
        end_close = float(future.iloc[-1]["close"])
        if hit_stop and not hit_t1:
            outcome, ret = "stop", (stop / entry - 1) * 100 if entry else 0
        elif hit_t2:
            outcome, ret = "target2", (target2 / entry - 1) * 100 if entry else 0
        elif hit_t1:
            outcome, ret = "target1", (target1 / entry - 1) * 100 if entry else 0
        else:
            outcome, ret = "expired", (end_close / entry - 1) * 100 if entry else 0
        row.update({"status": "closed", "outcome": outcome,
                    "outcome_return_pct": round(ret, 2), "closed_at": now})
        changed += 1
    if changed:
        _write(rows)
    return changed


def summary():
    rows = _read()
    closed = [r for r in rows if r.get("status") == "closed"]
    wins = [r for r in closed if r.get("outcome") in ("target1", "target2")]
    losses = [r for r in closed if r.get("outcome") == "stop"]
    returns = [float(r.get("outcome_return_pct")) for r in closed if r.get("outcome_return_pct") is not None]
    return {
        "total": len(rows), "closed": len(closed), "open": len(rows) - len(closed),
        "wins": len(wins), "losses": len(losses),
        "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
        "avg_return": round(sum(returns) / len(returns), 2) if returns else None,
        "profit_factor": round(sum(x for x in returns if x > 0) / abs(sum(x for x in returns if x < 0)), 2)
        if any(x < 0 for x in returns) else None,
    }


def backtest(history_loader, symbols, horizon=10):
    results = []
    for symbol in symbols:
        history = history_loader(symbol, days=400)
        if not history.get("success"):
            continue
        data = history.get("data", [])
        if len(data) < 120:
            continue
        frame = pd.DataFrame(data)
        for col in ("open", "high", "low", "close"):
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["high", "low", "close"]).sort_values("date").reset_index(drop=True)
        # Simple, non-lookahead test of the same ATR-based target/stop logic.
        for i in range(80, len(frame) - horizon):
            close = float(frame.iloc[i]["close"])
            tr = pd.concat([
                frame["high"] - frame["low"],
                (frame["high"] - frame["close"].shift()).abs(),
                (frame["low"] - frame["close"].shift()).abs()
            ], axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[i])
            if not atr or atr <= 0:
                continue
            entry, target, stop = close, close + atr, close - 1.2 * atr
            future = frame.iloc[i+1:i+horizon+1]
            ht = bool((future["high"] >= target).any())
            hs = bool((future["low"] <= stop).any())
            if ht and not hs:
                ret = (target / entry - 1) * 100
                outcome = "win"
            elif hs and not ht:
                ret = (stop / entry - 1) * 100
                outcome = "loss"
            else:
                ret = (float(future.iloc[-1]["close"]) / entry - 1) * 100
                outcome = "expired"
            results.append({"symbol": symbol, "outcome": outcome, "return_pct": ret})
    if not results:
        return {"success": False, "reason": "لا توجد بيانات كافية للـBacktest"}
    df = pd.DataFrame(results)
    wins = int((df.outcome == "win").sum())
    losses = int((df.outcome == "loss").sum())
    avg = float(df.return_pct.mean())
    pf = float(df.loc[df.return_pct > 0, "return_pct"].sum() / abs(df.loc[df.return_pct < 0, "return_pct"].sum())) if (df.return_pct < 0).any() else None
    return {"success": True, "samples": len(df), "wins": wins, "losses": losses,
            "win_rate": round(wins / len(df) * 100, 1), "avg_return": round(avg, 2),
            "profit_factor": round(pf, 2) if pf is not None else None}


def adaptive_feedback():
    """Return closed recommendation outcomes as ML feedback records."""
    return [r for r in _read() if r.get("status") == "closed" and r.get("outcome") in ("target1", "target2", "stop")]

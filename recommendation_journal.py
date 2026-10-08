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
        try:
            history = history_loader(row["symbol"], days=max(30, horizon + 5))
        except Exception:
            # One failed symbol must not prevent other recommendations from closing.
            continue
        data = history.get("data", []) if history.get("success") else []
        if not data:
            continue
        frame = pd.DataFrame(data)
        if "date" not in frame or "close" not in frame:
            continue
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["high"] = pd.to_numeric(frame["high"], errors="coerce") if "high" in frame else pd.Series(index=frame.index, dtype=float)
        frame["low"] = pd.to_numeric(frame["low"], errors="coerce") if "low" in frame else pd.Series(index=frame.index, dtype=float)
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
        if entry <= 0:
            continue

        # Evaluate the first barrier reached in chronological order. If a single
        # daily candle touches both a target and the stop, assume the stop happened
        # first; daily OHLC data cannot prove the intraday order.
        outcome, ret = "expired", None
        for candle in future.itertuples(index=False):
            candle_high = getattr(candle, "high", None)
            candle_low = getattr(candle, "low", None)
            if pd.notna(candle_low) and stop > 0 and float(candle_low) <= stop:
                outcome, ret = "stop", (stop / entry - 1) * 100
                break
            if pd.notna(candle_high) and target2 > 0 and float(candle_high) >= target2:
                outcome, ret = "target2", (target2 / entry - 1) * 100
                break
            if pd.notna(candle_high) and target1 > 0 and float(candle_high) >= target1:
                outcome, ret = "target1", (target1 / entry - 1) * 100
                break
        if ret is None:
            end_close = float(future.iloc[-1]["close"])
            ret = (end_close / entry - 1) * 100
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


def backtest(history_loader, symbols, horizon=10, min_score=60):
    """Walk-forward, no-lookahead backtest of the production-style ATR setup.

    The test evaluates each historical decision point using only data available
    up to that point. It reports return distribution, drawdown, profit factor,
    hit rate, and exposure so the strategy can be compared with a benchmark.
    """
    results = []
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for symbol in symbols:
        history = history_loader(symbol, days=1200)
        if not history.get("success"):
            continue
        data = history.get("data", [])
        if len(data) < 180:
            continue
        frame = pd.DataFrame(data).sort_values("date").reset_index(drop=True)
        for col in ("open", "high", "low", "close", "volume"):
            if col in frame:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["high","low","close"])
        # Recompute features only through each decision point.
        for i in range(90, len(frame) - horizon):
            hist = frame.iloc[:i+1].copy()
            close = float(hist.iloc[-1]["close"])
            if close <= 0:
                continue
            tr = pd.concat([
                hist["high"] - hist["low"],
                (hist["high"] - hist["close"].shift()).abs(),
                (hist["low"] - hist["close"].shift()).abs()
            ], axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[-1])
            sma20 = float(hist["close"].rolling(20).mean().iloc[-1])
            sma50 = float(hist["close"].rolling(50).mean().iloc[-1])
            rsi_delta = hist["close"].diff()
            gain = rsi_delta.clip(lower=0).rolling(14).mean().iloc[-1]
            loss = (-rsi_delta.clip(upper=0)).rolling(14).mean().iloc[-1]
            rsi = float(100 - 100/(1 + gain/loss)) if pd.notna(gain) and pd.notna(loss) and loss != 0 else 50.0
            volume_ratio = None
            if "volume" in hist:
                avgv = hist["volume"].rolling(20).mean().iloc[-1]
                if pd.notna(avgv) and avgv:
                    volume_ratio = float(hist["volume"].iloc[-1] / avgv)
            # Conservative entry filter: trend + momentum + non-extreme RSI + liquidity.
            score = 0
            score += 20 if close > sma20 else 0
            score += 20 if close > sma50 else 0
            score += 15 if sma20 > sma50 else 0
            score += 20 if 45 <= rsi <= 68 else 0
            score += 15 if volume_ratio is None or volume_ratio >= 0.7 else 0
            score += 10 if hist["close"].pct_change(20).iloc[-1] > 0 else 0
            if score < min_score or not atr or atr <= 0:
                continue
            target = close + atr
            stop = close - 1.2 * atr
            future = frame.iloc[i+1:i+horizon+1]
            ht = bool((future["high"] >= target).any())
            hs = bool((future["low"] <= stop).any())
            # Daily OHLC cannot establish intraday barrier order; if both are
            # touched in the same horizon, stop-first is the conservative assumption.
            if hs:
                ret = (stop/close-1)*100
                outcome="loss"
            elif ht:
                ret = (target/close-1)*100
                outcome="win"
            else:
                ret = (float(future.iloc[-1]["close"])/close-1)*100
                outcome="expired"
            results.append({"symbol":symbol,"date":str(frame.iloc[i]["date"]),
                            "score":score,"return_pct":ret,"outcome":outcome})
            equity *= 1 + ret/100 * 0.25
            peak=max(peak,equity)
            max_dd=max(max_dd,(peak-equity)/peak*100)

    if not results:
        return {"success":False,"reason":"لا توجد بيانات كافية للـWalk-forward Backtest"}
    df=pd.DataFrame(results)
    wins=int((df.outcome=="win").sum())
    losses=int((df.outcome=="loss").sum())
    positive=df.loc[df.return_pct>0,"return_pct"].sum()
    negative=abs(df.loc[df.return_pct<0,"return_pct"].sum())
    avg=float(df.return_pct.mean())
    return {
        "success":True,
        "method":"Walk-forward / no-lookahead / ATR target-stop",
        "samples":int(len(df)),
        "symbols_tested":int(df.symbol.nunique()),
        "wins":wins,"losses":losses,
        "win_rate":round(wins/len(df)*100,1),
        "avg_return":round(avg,2),
        "median_return":round(float(df.return_pct.median()),2),
        "profit_factor":round(float(positive/negative),2) if negative else None,
        "max_drawdown":round(float(max_dd),2),
        "best_trade":round(float(df.return_pct.max()),2),
        "worst_trade":round(float(df.return_pct.min()),2),
        "positive_return_rate":round(float((df.return_pct>0).mean()*100),1),
    }


def adaptive_feedback():
    """Return closed recommendation outcomes as ML feedback records."""
    return [r for r in _read() if r.get("status") == "closed" and r.get("outcome") in ("target1", "target2", "stop")]

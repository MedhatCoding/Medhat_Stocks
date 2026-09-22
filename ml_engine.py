import numpy as np
import pandas as pd

FEATURES = ["rsi14","return20","return60","volatility20","volume_ratio","atr_pct","distance_support_pct","trend20","trend50"]

def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

def train_and_predict(frame, horizon=10, target_pct=3.0, stop_pct=4.0):
    if frame is None or len(frame) < 90:
        return {"success": False, "reason": "بيانات تاريخية غير كافية لتدريب النموذج"}
    w = frame.copy().reset_index(drop=True)
    close = pd.to_numeric(w["close"], errors="coerce")
    x = pd.DataFrame(index=w.index)
    x["rsi14"] = pd.to_numeric(w.get("rsi14"), errors="coerce")
    x["return20"] = close.pct_change(20) * 100
    x["return60"] = close.pct_change(60) * 100
    x["volatility20"] = close.pct_change().rolling(20).std() * np.sqrt(252) * 100
    volume = pd.to_numeric(w.get("volume"), errors="coerce")
    x["volume_ratio"] = volume / volume.rolling(20).mean()
    atr = pd.to_numeric(w.get("atr14"), errors="coerce")
    x["atr_pct"] = atr / close * 100
    support = pd.to_numeric(w["low"], errors="coerce").rolling(60).min()
    x["distance_support_pct"] = (close - support) / close * 100
    sma20, sma50 = close.rolling(20).mean(), close.rolling(50).mean()
    x["trend20"], x["trend50"] = close / sma20 - 1, close / sma50 - 1
    x = x.replace([np.inf,-np.inf],np.nan)
    y = []
    for i in range(len(w)):
        if i + horizon >= len(w):
            y.append(np.nan); continue
        entry = close.iloc[i]
        highs = pd.to_numeric(w["high"], errors="coerce").iloc[i+1:i+horizon+1]
        lows = pd.to_numeric(w["low"], errors="coerce").iloc[i+1:i+horizon+1]
        hit_target = bool((highs >= entry*(1+target_pct/100)).any())
        hit_stop = bool((lows <= entry*(1-stop_pct/100)).any())
        y.append(1.0 if hit_target and not hit_stop else 0.0)
    y = pd.Series(y)
    valid = x.notna().all(axis=1) & y.notna()
    idx = np.where(valid.values)[0]
    if len(idx) < 45 or len(np.unique(y.iloc[idx])) < 2:
        return {"success": False, "reason": "عدد عينات التدريب غير كافٍ"}
    split = max(30, int(len(idx)*0.8))
    fit, val = idx[:split], idx[split:]
    mu, sd = x.iloc[fit].mean(), x.iloc[fit].std().replace(0,1).fillna(1)
    X = ((x-mu)/sd).to_numpy(float); Y = y.to_numpy(float)
    ww, b = np.zeros(X.shape[1]), 0.0
    for _ in range(700):
        p = _sigmoid(X[fit]@ww+b); e = p-Y[fit]
        ww -= 0.025*((X[fit].T@e)/len(fit)+0.01*ww); b -= 0.025*float(e.mean())
    latest = len(w)-1
    if not x.iloc[latest].notna().all():
        return {"success": False, "reason": "بيانات أحدث جلسة غير مكتملة للنموذج"}
    p = float(_sigmoid(((x.iloc[latest]-mu)/sd).to_numpy(float)@ww+b))
    accuracy = None
    if len(val) >= 8:
        accuracy = float(np.mean((_sigmoid(X[val]@ww+b)>=0.5)==Y[val]))
    return {"success":True,"probability":round(p*100,1),"samples":int(len(fit)),
            "validation_samples":int(len(val)),
            "validation_accuracy":round(accuracy*100,1) if accuracy is not None else None,
            "target_pct":target_pct,"stop_pct":stop_pct,"horizon_days":horizon,
            "method":"Logistic regression / historical walk-forward"}

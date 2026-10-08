import numpy as np
import pandas as pd

FEATURES = ["rsi14","return20","return60","volatility20","volume_ratio","atr_pct","distance_support_pct","trend20","trend50"]

def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

def _prepare(frame, feedback=None):
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
    y = []
    horizon, target_pct, stop_pct = 10, 3.0, 4.0
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
    feedback_rows = []
    for item in (feedback or []):
        features = item.get("features") or {}
        outcome = item.get("outcome")
        if outcome not in ("target1","target2","stop"): continue
        row = {name: pd.to_numeric(features.get(name), errors="coerce") for name in FEATURES}
        row["_target"] = 1.0 if outcome in ("target1","target2") else 0.0
        if all(pd.notna(row[name]) for name in FEATURES): feedback_rows.append(row)
    if feedback_rows:
        fx = pd.DataFrame([{k:v for k,v in r.items() if k!="_target"} for r in feedback_rows])
        fy = pd.Series([r["_target"] for r in feedback_rows])
        x = pd.concat([x,fx],ignore_index=True); y = pd.concat([y,fy],ignore_index=True)
    x=x.replace([np.inf,-np.inf],np.nan)
    valid=x.notna().all(axis=1)&y.notna()
    idx=np.where(valid.values)[0]
    return x,y,idx

def _fit_logistic(X,Y,steps=700,lr=0.025):
    w=np.zeros(X.shape[1]); b=0.0
    for _ in range(steps):
        p=_sigmoid(X@w+b); e=p-Y
        w-=lr*((X.T@e)/len(Y)+0.01*w); b-=lr*float(e.mean())
    return lambda z:_sigmoid(z@w+b)

def _relu(z): return np.maximum(z,0.0)

def _fit_mlp(X,Y,seed=42,epochs=450,lr=0.012):
    rng=np.random.default_rng(seed)
    sizes=[X.shape[1],16,10,6,1]
    W=[rng.normal(0,np.sqrt(2/sizes[i]),(sizes[i],sizes[i+1])) for i in range(len(sizes)-1)]
    B=[np.zeros(sizes[i+1]) for i in range(len(sizes)-1)]
    for _ in range(epochs):
        A=[X]
        Z=[]
        for i in range(len(W)-1):
            z=A[-1]@W[i]+B[i]; Z.append(z); A.append(_relu(z))
        z=A[-1]@W[-1]+B[-1]; Z.append(z); A.append(_sigmoid(z))
        dz=(A[-1]-Y[:,None])
        for i in reversed(range(len(W))):
            a_prev=A[i]
            W[i]-=lr*(a_prev.T@dz/len(Y))
            B[i]-=lr*dz.mean(axis=0)
            if i>0:
                dz=(dz@W[i].T)*(Z[i-1]>0)
    def predict(X2):
        a=X2
        for i in range(len(W)-1): a=_relu(a@W[i]+B[i])
        return _sigmoid(a@W[-1]+B[-1]).ravel()
    return predict

def train_and_predict(frame,horizon=10,target_pct=3.0,stop_pct=4.0,feedback=None):
    if frame is None or len(frame)<90:
        return {"success":False,"reason":"بيانات تاريخية غير كافية لتدريب النماذج"}
    x,y,idx=_prepare(frame,feedback=feedback)
    if len(idx)<45 or len(np.unique(y.iloc[idx]))<2:
        return {"success":False,"reason":"عدد عينات التدريب غير كافٍ"}
    split=max(30,int(len(idx)*0.8))
    fit,val=idx[:split],idx[split:]
    mu=x.iloc[fit].mean(); sd=x.iloc[fit].std().replace(0,1).fillna(1)
    X=((x-mu)/sd).to_numpy(float); Y=y.to_numpy(float)
    logit=_fit_logistic(X[fit],Y[fit])
    mlp=_fit_mlp(X[fit],Y[fit])
    latest=len(frame)-1
    if not x.iloc[latest].notna().all():
        return {"success":False,"reason":"بيانات أحدث جلسة غير مكتملة للنماذج"}
    p1=float(logit(X[[latest]])[0]); p2=float(mlp(X[[latest]])[0])
    ensemble=(p1*0.45+p2*0.55)*100
    acc_log=acc_mlp=None
    if len(val)>=8:
        acc_log=float(np.mean((logit(X[val])>=0.5)==Y[val]))
        acc_mlp=float(np.mean((mlp(X[val])>=0.5)==Y[val]))
    return {
        "success":True,"probability":round(ensemble,1),
        "logistic_probability":round(p1*100,1),"deep_learning_probability":round(p2*100,1),
        "samples":int(len(fit)),"validation_samples":int(len(val)),
        "validation_accuracy":round(((acc_log*0.45+acc_mlp*0.55)*100),1) if acc_log is not None and acc_mlp is not None else None,
        "logistic_accuracy":round(acc_log*100,1) if acc_log is not None else None,
        "deep_learning_accuracy":round(acc_mlp*100,1) if acc_mlp is not None else None,
        "target_pct":target_pct,"stop_pct":stop_pct,"horizon_days":horizon,
        "method":"Ensemble: logistic regression + 3-hidden-layer neural network + walk-forward feedback",
        "feedback_samples":sum(1 for r in (feedback or []) if r.get("outcome") in ("target1","target2","stop")),
    }

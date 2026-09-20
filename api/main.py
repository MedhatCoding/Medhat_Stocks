import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data_engine import DataEngine

app = FastAPI(title="Medhat Stocks API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DataEngine()

@app.get("/health")
def health():
    return engine.health_check()

@app.get("/stocks/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=50)):
    return {"success": True, "data": engine.search_symbols(q, limit=limit)}

@app.get("/stocks/{symbol}/latest")
def latest(symbol: str):
    result = engine.get_latest_price(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "لا توجد بيانات"))
    return result

@app.get("/stocks/{symbol}/analysis")
def analysis(symbol: str):
    result = engine.analyze_stock(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "تعذر التحليل"))
    return result

@app.get("/stocks/{symbol}/fundamentals")
def fundamentals(symbol: str):
    result = engine.get_fundamentals(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "تعذر جلب البيانات"))
    return result

@app.post("/stocks/{symbol}/ai-analysis")
def ai_analysis(symbol: str):
    result = engine.ai_analysis(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "تعذر تحليل الذكاء الاصطناعي"))
    return result

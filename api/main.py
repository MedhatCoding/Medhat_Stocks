import os

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

@app.get("/stocks/{symbol}/live")
def live(symbol: str):
    result = engine.get_live_quote(symbol)
    if result.get("success"):
        return result
    result = engine.get_latest_price(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "لا توجد بيانات"))
    return {"success": True, "data": result, "provider": "EODHD"}

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

@app.get("/market/context")
def market_context():
    return engine.get_market_context()

@app.get("/opportunities")
def opportunities(limit: int = Query(20, ge=1, le=40)):
    result = engine.get_opportunities(limit=limit)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "تعذر تحميل الفرص"))
    return result

@app.get("/stocks/{symbol}/full-analysis")
def full_analysis(symbol: str):
    result = engine.get_full_analysis(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "تعذر التحليل"))
    return result

@app.get("/stocks/{symbol}/news")
def stock_news(symbol: str, limit: int = Query(8, ge=1, le=20)):
    result = engine.get_news(symbol, limit=limit)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "تعذر جلب الأخبار"))
    return result

@app.get("/stocks/{symbol}/sharia")
def sharia(symbol: str):
    from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE, REFERENCE_SOURCE
    code = engine.display_symbol(symbol)
    return {
        "symbol": code,
        "compliant": code in SHARIA_SYMBOLS,
        "source": REFERENCE_SOURCE,
        "reference_date": REFERENCE_DATE,
        "reference_count": len(SHARIA_SYMBOLS),
    }

@app.get("/stocks/{symbol}/fundamentals")
def fundamentals(symbol: str):
    result = engine.get_fundamentals(symbol)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "تعذر جلب البيانات"))
    return result

@app.post("/stocks/{symbol}/ai-analysis")
def ai_analysis(symbol: str):
    technical = engine.analyze_stock(symbol)
    if not technical.get("success"):
        raise HTTPException(status_code=404, detail=technical.get("error", "تعذر التحليل"))
    fundamentals = engine.get_company_snapshot(symbol)
    result = engine.ai_analysis(
        symbol,
        technical,
        fundamentals if fundamentals.get("success") else {},
    )
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "تعذر تحليل الذكاء الاصطناعي"))
    return result

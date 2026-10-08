"""Run the production-style EGX walk-forward backtest.

Usage:
  python scripts/backtest.py

Results are written to backtest_report.json and can be inspected from CI.
"""
import json
from pathlib import Path

from data_engine import DataEngine
from recommendation_journal import backtest
from sharia_universe import SHARIA_SYMBOLS

engine = DataEngine()
result = backtest(engine.get_stock_history, SHARIA_SYMBOLS, horizon=10, min_score=60)
Path("backtest_report.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, indent=2))
if not result.get("success"):
    raise SystemExit(1)

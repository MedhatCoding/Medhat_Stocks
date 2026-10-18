"""Check the latest official Boubyan Egypt Sharia list without silently changing the active universe.

This job is intentionally fail-safe: it discovers the current official PDF and extracts
text/ticker candidates for review; it never promotes uncertain PDF parsing to approved
symbols automatically.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from pypdf import PdfReader
from io import BytesIO

SOURCE_PAGE = "https://www.boubyancapital.com/brokerage/"
OUT = Path("artifacts/sharia_source_check.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MedhatStocks-ShariaSourceCheck/1.0)"}
TICKER_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,5}\b")


def main():
    response = requests.get(SOURCE_PAGE, headers=HEADERS, timeout=25)
    response.raise_for_status()
    html = response.text
    links = re.findall(r'href=["\']([^"\']*egypt-list-[^"\']+\.pdf)["\']', html, flags=re.I)
    links = [urljoin(SOURCE_PAGE, x.replace("&amp;", "&")) for x in links]
    if not links:
        raise RuntimeError("No official Egypt Sharia PDF link found on Boubyan brokerage page")
    # Prefer latest quarter/year encoded in the filename; retain page order as tie-break.
    def rank(url):
        m = re.search(r"egypt-list-q([1-4])-(20\d{2})", url, re.I)
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)
    pdf_url = sorted(dict.fromkeys(links), key=rank, reverse=True)[0]
    pdf_response = requests.get(pdf_url, headers=HEADERS, timeout=35)
    pdf_response.raise_for_status()
    if not pdf_response.content.startswith(b"%PDF"):
        raise RuntimeError("Official source link did not return PDF bytes")
    reader = PdfReader(BytesIO(pdf_response.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text.strip()) < 500:
        raise RuntimeError("PDF text extraction produced too little text; keeping last-known-good universe")
    # This is a diagnostic candidate list, not an approved replacement.
    tokens = sorted(set(TICKER_RE.findall(text)))
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_page": SOURCE_PAGE,
        "source_pdf": pdf_url,
        "pdf_pages": len(reader.pages),
        "extracted_text_characters": len(text),
        "ticker_candidates": tokens,
        "ticker_candidate_count": len(tokens),
        "status": "source_retrieved_needs_validation",
        "active_universe_changed": False,
        "note": "PDF token extraction is diagnostic only; candidates are not auto-approved as Sharia-compliant.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("source_pdf", "pdf_pages", "ticker_candidate_count", "status")}, indent=2))
    if len(tokens) < 50 or len(tokens) > 180:
        raise RuntimeError(f"Suspicious ticker candidate count ({len(tokens)}); active universe unchanged")


if __name__ == "__main__":
    main()

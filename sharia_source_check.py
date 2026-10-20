"""Diagnostic-only check of Boubyan's published Egypt Sharia list.

Never changes the approved universe automatically. A failed/stale source URL is
recorded as a report so that external-source outages do not mask app test results.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

import requests
from pypdf import PdfReader

SOURCE_PAGE = "https://www.boubyancapital.com/brokerage/"
OUT = Path("artifacts/sharia_source_check.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MedhatStocks-ShariaSourceCheck/1.1)"}
TICKER_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,5}\b")


def save_report(report):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_page": SOURCE_PAGE,
        "source_pdf": None,
        "pdf_pages": 0,
        "extracted_text_characters": 0,
        "ticker_candidates": [],
        "ticker_candidate_count": 0,
        "status": "source_check_failed",
        "active_universe_changed": False,
        "note": "Diagnostic only; source failures never modify the approved universe.",
    }
    try:
        response = requests.get(SOURCE_PAGE, headers=HEADERS, timeout=25)
        response.raise_for_status()
        links = re.findall(r'href=["\']([^"\']*egypt-list-[^"\']+\.pdf)["\']', response.text, flags=re.I)
        links = [urljoin(SOURCE_PAGE, link.replace("&amp;", "&")) for link in links]
        # Keep going even when the landing page temporarily omits its PDF link:
        # a known official archive PDF can still provide a clearly labelled stale
        # diagnostic instead of turning the whole audit into a blind spot.
        report["official_pdf_links_discovered"] = len(links)

        def rank(url):
            match = re.search(r"egypt-list-q([1-4])-(20\d{2})", url, re.I)
            return (int(match.group(2)), int(match.group(1))) if match else (0, 0)

        # The official page sometimes points to a missing newer PDF. Add a known
        # older official PDF as a diagnostic-only fallback; it is explicitly marked stale.
        stale_official_fallbacks = [
            "https://boubyancapital.com/media/filer_public/3b/b7/3bb7ef35-d699-4d91-b9c8-0123ef52bfd3/egypt-list-q1-2025.pdf"
        ]
        discovered = sorted(dict.fromkeys(links), key=rank, reverse=True)
        ordered = discovered + [u for u in stale_official_fallbacks if u not in discovered]
        report["official_pdf_urls_discovered"] = discovered
        report["fallback_pdf_urls_configured"] = len(stale_official_fallbacks)
        errors = []
        for pdf_url in ordered:
            try:
                pdf_response = requests.get(pdf_url, headers=HEADERS, timeout=35)
                pdf_response.raise_for_status()
                if not pdf_response.content.startswith(b"%PDF"):
                    raise RuntimeError("URL did not return PDF bytes")
                reader = PdfReader(BytesIO(pdf_response.content))
                extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
                if len(extracted.strip()) < 500:
                    raise RuntimeError("PDF text extraction produced too little text")
                tokens = sorted(set(TICKER_RE.findall(extracted)))
                try:
                    from sharia_universe import SHARIA_SYMBOLS
                    active_symbols = set(SHARIA_SYMBOLS)
                except Exception:
                    active_symbols = set()
                report.update({
                    "active_reference_count": len(active_symbols),
                    "extracted_candidates_not_in_reference": sorted(set(tokens) - active_symbols),
                    "reference_symbols_not_extracted": sorted(active_symbols - set(tokens)),
                    "comparison_note": "Text-token comparison is a review aid only; it can contain false positives/negatives and never changes the active universe.",
                    "source_pdf": pdf_url,
                    "pdf_pages": len(reader.pages),
                    "extracted_text_characters": len(extracted),
                    "ticker_candidates": tokens,
                    "ticker_candidate_count": len(tokens),
                    "status": "source_retrieved_needs_validation",
                    "note": "PDF token extraction is diagnostic only; candidates are not auto-approved as Sharia-compliant.",
                })
                if pdf_url in stale_official_fallbacks:
                    report["status"] = "stale_official_fallback_needs_refresh"
                    report["note"] += " This is an older official PDF fallback, not a current certification."
                if not 50 <= len(tokens) <= 180:
                    report["status"] = "source_retrieved_suspicious_extraction"
                    report["note"] += " Candidate count outside expected range; review required."
                save_report(report)
                print(json.dumps({k: report[k] for k in ("source_pdf", "pdf_pages", "ticker_candidate_count", "status")}, indent=2))
                return
            except Exception as exc:
                errors.append(f"{pdf_url}: {exc}")
        if not ordered:
            raise RuntimeError("No official Egypt Sharia PDF link was discovered and no fallback was configured")
        raise RuntimeError("All discovered official PDF links and configured fallbacks failed: " + " | ".join(errors))
    except Exception as exc:
        report["error"] = str(exc)
        save_report(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        # Do not fail the whole app validation for an external source outage.
        return


if __name__ == "__main__":
    main()

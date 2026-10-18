"""Reference universe for Sharia-compliant EGX equities.

IMPORTANT:
- This is a dated reference list, not a permanent religious ruling.
- EGX33 constituents are NOT the complete universe of Sharia-compliant shares.
- Never add every EGX-listed share automatically as Sharia-compliant. New names
  must be verified against a documented screening methodology/source.
- The app may discover additional EGX-listed symbols separately, but those
  belong in a review queue until their Sharia status is verified.
"""

REFERENCE_DATE = "2026-09-01"
REFERENCE_SOURCE = "Boubyan Capital Egypt Sharia list (Q1 2026) + EGX September 2026 EGX33 Shariah review"
REFERENCE_STATUS = "dated_reference_not_live_certification"

SHARIA_SYMBOLS = [
    "AALR","ACGC","ACRO","ADIB","AIFI","AITG","AIVCB","ALUM","AMER","AMES",
    "AMIA","AMOC","APPC","APSW","ARCC","ARVA","ASHC","ATLC","ATQA","AXPH",
    "BIOC","BTFH","CAED","CLHO","COSG","CPCI","DAPH","DCRC","DPKP","EALR",
    "EFIC","EFID","EGAL","EGAS","ELKA","ELNA","EMRI","ETRS","FAIT","FAITA",
    "GGCC","GIHD","GMCI","GOUR","GSSC","GTHE","IDHC","IFAP","INFI","IRON","ISMA",
    "ISMQ","JUFO","KABO","MAAL","MBEG","MASR","MBSC","MCQE","MCRO","MEPA",
    "MFPC","MICH","MILS","MOED","MPCO","MTIE","NCEM","NCGC","NDRL","NEDA",
    "NIPH","NOAF","ORAS","PACH","PHDC","PRDC","RACC","RMDA","RREI","RUBX",
    "SAUD","SCEM","SIPC","SMCS","SMFR","SPIN","SPMD","SUCE","SUGR","SVCE",
    "SWDY","TALM","TRSI","VODE","WATP","ZEOT",
]

# Deduplicate aliases without silently inflating the universe size.
SHARIA_SYMBOLS = list(dict.fromkeys(s.strip().upper().replace(".CA", "").replace(".EGX", "")
                                    for s in SHARIA_SYMBOLS if s and s.strip()))

def is_sharia_reference(symbol):
    """True only for symbols in the dated, documented reference list."""
    code = (symbol or "").strip().upper().split(".")[0]
    return code in SHARIA_SYMBOLS

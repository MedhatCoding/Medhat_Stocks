"""Sharia screening universe.

The baseline below is the Egypt Q1-2026 Sharia-compliant list issued by
Boubyan Capital on 2026-06-08. The application treats it as a reference
universe, not as a permanent religious ruling. Update the list when the
source is revised.
"""

REFERENCE_DATE = "2026-06-08"
REFERENCE_SOURCE = "Boubyan Capital - Egypt Sharia Compliant Companies Q1 2026; unioned with official EGX33 Shariah constituents"

# EGX33 constituents are Sharia-screened by the Egyptian Exchange/FRA methodology.
# This is deliberately a union, not a restriction to index membership: the
# Boubyan list also contains eligible stocks outside EGX33.
EGX33_SYMBOLS = [
    "RACC", "TALM", "ISPH", "ABUK", "EMFD", "AMOC", "OCDI", "SWDY",
    "ACGC", "ECAP", "ETRS", "ETEL", "ORWE", "MTIE", "JUFO", "ADIB",
    "FAIT", "FAITA", "GGCC", "IDHC", "PHDC", "MASR", "ORAS", "EGAL",
    "MFPC", "SKPC", "CLHO", "FWRY", "EAST", "TMGH", "SODIC", "MBEG",
    "BTFH", "GOUR",
]

SHARIA_SYMBOLS = [
    "AALR","ACGC","ACRO","ADIB","AIFI","AITG","AIVCB","ALUM","AMER","AMES",
    "AMIA","AMOC","APPC","APSW","ARCC","ARVA","ASHC","ATLC","ATQA","AXPH",
    "BIOC","BTFH","CAED","CLHO","COSG","CPCI","DAPH","DCRC","DPKP","EALR",
    "EFIC","EFID","EGAL","EGAS","ELKA","ELNA","EMRI","ETRS","FAIT","FAITA",
    "GGCC","GIHD","GMCI","GSSC","GTHE","IDHC","IFAP","INFI","IRON","ISMA",
    "ISMQ","JUFO","KABO","MAAL","MBEG","MASR","MBSC","MCQE","MCRO","MEPA",
    "MFPC","MICH","MILS","MOED","MPCO","MTIE","NCEM","NCGC","NDRL","NEDA",
    "NIPH","NOAF","ORAS","PACH","PHDC","PRDC","RACC","RMDA","RREI","RUBX",
    "SAUD","SCEM","SIPC","SMCS","SMFR","SPIN","SPMD","SUCE","SUGR","SVCE",
    "SWDY","TALM","TRSI","VODE","WATP","ZEOT",
]

# Combined reference universe. The list is not capped at 96 and includes
# EGX33 constituents even when the external quarterly list differs.
SHARIA_SYMBOLS = list(dict.fromkeys(SHARIA_SYMBOLS + EGX33_SYMBOLS))

# Optional additions are configured via SHARIA_EXTRA_SYMBOLS. They should only
# be used for symbols verified against a current Sharia screening source.
def get_sharia_universe(extra_symbols=None):
    extras = extra_symbols or []
    normalized = [str(x).strip().upper().replace(".EGX", "").replace(".CA", "")
                  for x in extras if str(x).strip()]
    return list(dict.fromkeys(SHARIA_SYMBOLS + normalized))

def is_sharia_reference(symbol):
    code = (symbol or "").strip().upper().replace(".EGX", "").replace(".CA", "")
    return code in SHARIA_SYMBOLS

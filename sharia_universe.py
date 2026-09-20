"""Sharia screening universe.

The baseline below is the Egypt Q1-2026 Sharia-compliant list issued by
Boubyan Capital on 2026-06-08. The application treats it as a reference
universe, not as a permanent religious ruling. Update the list when the
source is revised.
"""

REFERENCE_DATE = "2026-06-08"
REFERENCE_SOURCE = "Boubyan Capital - Egypt Sharia Compliant Companies Q1 2026"

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

def is_sharia_reference(symbol):
    return (symbol or "").strip().upper().replace(".EGX", "") in SHARIA_SYMBOLS

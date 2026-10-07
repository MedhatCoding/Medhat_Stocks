"""Shariah index-tracking funds available in Egypt.

The two funds below explicitly track the EGX33 Shariah index.
They are analyzed separately from the individual-stock Shariah universe.
"""

SHARIAH_INDEX_FUNDS = [
    {
        "symbol": "BWA",
        "name": "بلتون وفرة للاستثمار في أسهم مؤشر الشريعة EGX33",
        "type": "صندوق مؤشر",
        "benchmark": "EGX33 Shariah",
        "manager": "بلتون لإدارة صناديق الاستثمار",
    },
    {
        "symbol": "CSF",
        "name": "مصر شريعة إكويتي - للاستثمار في مؤشر الشريعة EGX33",
        "type": "صندوق مؤشر",
        "benchmark": "EGX33 Shariah",
        "manager": "سي آي لإدارة الأصول",
    },
]

SHARIAH_FUND_MAP = {x["symbol"]: x for x in SHARIAH_INDEX_FUNDS}

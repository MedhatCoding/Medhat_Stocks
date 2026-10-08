"""Egyptian gold investment funds used as a defensive asset sleeve.

The app keeps these separate from Sharia-compliant EGX equities. A fund is only
marked Sharia-compliant when the available source explicitly confirms it.
"""
GOLD_FUNDS = [
    {"symbol":"AZG","name":"AZ-Gold","manager":"أزيموت مصر","type":"صندوق ذهب","sharia_compliant":True},
    {"symbol":"BSB","name":"بلتون إيفولف - سبائك","manager":"بلتون / إيفولف","type":"صندوق ذهب","sharia_compliant":False},
    {"symbol":"ADA","name":"الأهلي دهب","manager":"الأهلي لإدارة الاستثمارات المالية / إيفولف","type":"صندوق ذهب","sharia_compliant":False},
    {"symbol":"CGO","name":"CI Gold Fund","manager":"CI Asset Management","type":"صندوق ذهب","sharia_compliant":False},
    {"symbol":"MGO","name":"Mubasher Gold","manager":"Mubasher Asset Management","type":"صندوق ذهب","sharia_compliant":False},
    {"symbol":"HGO","name":"Hermes Gold","manager":"Hermes Portfolio & Fund Management","type":"صندوق ذهب","sharia_compliant":False},
]
GOLD_FUND_MAP = {x["symbol"]: x for x in GOLD_FUNDS}

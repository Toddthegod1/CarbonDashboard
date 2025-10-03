import csv
import io
from datetime import datetime
from sqlalchemy import text

def month_bounds(year:int, month:int):
    from calendar import monthrange
    start = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59)
    return start, end

def build_monthly_csv(db, year, month) -> bytes:
    start, end = month_bounds(year, month)
    rows = db.execute(text("""
        SELECT ts, category, amount, unit, kg_co2e, note
        FROM activities
        WHERE ts >= :s AND ts <= :e
        ORDER BY ts ASC
    """), {"s": start, "e": end}).fetchall()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["timestamp","category","amount","unit","kg_co2e","note"])
    total = 0.0
    for r in rows:
        w.writerow([r.ts.isoformat(timespec="seconds"), r.category, float(r.amount), r.unit, float(r.kg_co2e), r.note or ""])
        total += float(r.kg_co2e)
    w.writerow([])
    w.writerow(["TOTAL","","","", total, "kg CO2e"])
    return out.getvalue().encode("utf-8")
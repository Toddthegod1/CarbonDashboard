from sqlalchemy import text
from .db import get_db

def get_factor(category: str, unit: str):
    db = get_db()
    row = db.execute(
        text("SELECT kg_co2e_per_unit FROM emissions_factors WHERE category=:c AND unit=:u LIMIT 1"),
        {"c": category, "u": unit}
    ).fetchone()
    return float(row[0]) if row else None
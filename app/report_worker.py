import os
import traceback
import boto3
from datetime import datetime
from sqlalchemy import create_engine, text
from .config import Config
from .report_lib import build_monthly_csv

def run_once():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    bucket = Config.S3_BUCKET

    with engine.begin() as conn:
        # find one pending
        r = conn.execute(text("""
            SELECT id, period_year, period_month FROM reports
            WHERE status='PENDING'
            ORDER BY created_at ASC
            LIMIT 1
        """)).fetchone()

        if not r:
            return "no-pending"

        rid, year, month = r.id, r.period_year, r.period_month
        # mark IN-PROGRESS
        conn.execute(text("UPDATE reports SET status='INPROGRESS', updated_at=NOW() WHERE id=:id"), {"id": rid})

    try:
        with engine.begin() as conn:
            csv_bytes = build_monthly_csv(conn, year, month)
        key = f"reports/{year:04d}-{month:02d}.csv"
        s3.put_object(Bucket=bucket, Key=key, Body=csv_bytes, ContentType="text/csv")
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE reports SET status='COMPLETE', s3_key=:k, updated_at=NOW() WHERE id=:id
            """), {"k": key, "id": rid})
        return f"done:{key}"
    except Exception as e:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE reports SET status='ERROR', updated_at=NOW() WHERE id=:id
            """), {"id": rid})
        traceback.print_exc()
        return f"error:{rid}"

if __name__ == "__main__":
    print(run_once())
# app/report_worker.py
import os
import io
import traceback
import boto3
from datetime import datetime
from sqlalchemy import create_engine, text

from .config import Config
from .report_lib import build_monthly_csv


def _log(msg: str):
    # Simple stdout logging so `journalctl -u carbon-worker` shows progress
    print(f"[worker] {datetime.utcnow().isoformat()}Z {msg}", flush=True)


def run_once():
    """
    Process exactly ONE pending report:
      1) Find oldest PENDING row
      2) Mark INPROGRESS
      3) Build CSV bytes for that period
      4) Upload to S3 (public-read)
      5) Update row to COMPLETE with s3_key
    Returns a short status string for logs.
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    bucket = Config.S3_BUCKET

    # 1) find one pending
    with engine.begin() as conn:
        r = conn.execute(text("""
            SELECT id, period_year, period_month
            FROM reports
            WHERE status = 'PENDING'
            ORDER BY created_at ASC
            LIMIT 1
        """)).fetchone()

        if not r:
            _log("no pending reports")
            return "no-pending"

        rid, year, month = r.id, int(r.period_year), int(r.period_month)
        _log(f"picked report id={rid} period={year:04d}-{month:02d}")

        # 2) mark INPROGRESS
        conn.execute(
            text("UPDATE reports SET status='INPROGRESS', updated_at=NOW() WHERE id=:id"),
            {"id": rid},
        )

    try:
        # 3) build CSV bytes for that month
        with engine.begin() as conn:
            # build_monthly_csv should return bytes (CSV)
            csv_bytes = build_monthly_csv(conn, year, month)

        # 4) upload to S3 with public-read so direct link works
        key = f"reports/{year:04d}-{month:02d}.csv"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_bytes,
            ContentType="text/csv",
            ACL="public-read",  # make it public
        )
        _log(f"uploaded s3://{bucket}/{key} (public-read)")

        # 5) update DB to COMPLETE
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE reports
                    SET status='COMPLETE', s3_key=:k, updated_at=NOW()
                    WHERE id=:id
                """),
                {"k": key, "id": rid},
            )
        _log(f"marked COMPLETE id={rid}")
        return f"done:{key}"

    except Exception as e:
        # mark ERROR and log traceback
        _log(f"ERROR while processing id={rid}: {e}")
        traceback.print_exc()
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE reports SET status='ERROR', updated_at=NOW() WHERE id=:id"),
                {"id": rid},
            )
        return f"error:{rid}"


if __name__ == "__main__":
    print(run_once())
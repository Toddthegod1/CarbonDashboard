from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy import text
from .db import get_db
from .factors import get_factor

# NEW imports for S3 presigned URLs and "now" convenience
import os
import boto3
from datetime import datetime

bp = Blueprint("main", __name__)

# Reuse AWS + S3 settings from env (same values you put in .env)
S3_BUCKET = os.environ.get("S3_BUCKET")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
s3 = boto3.client("s3", region_name=AWS_REGION)

@bp.route("/")
def index():
    db = get_db()
    totals = db.execute(text("""
        SELECT category, unit, COUNT(*) as entries,
               SUM(amount) as total_amount,
               SUM(kg_co2e) as total_kg
        FROM activities
        GROUP BY category, unit
        ORDER BY total_kg DESC
    """)).fetchall()
    grand = db.execute(text("SELECT COALESCE(SUM(kg_co2e),0) FROM activities")).scalar()
    return render_template("index.html", totals=totals, grand=grand)

@bp.route("/add", methods=["GET","POST"])
def add_activity():
    if request.method == "POST":
        category = request.form["category"]
        amount = float(request.form["amount"])
        unit = request.form["unit"]
        note = request.form.get("note","").strip()
        factor = get_factor(category, unit)
        if factor is None:
            flash("No emissions factor for that category/unit. Add one or pick another.", "error")
            return redirect(url_for("main.add_activity"))
        kg = amount * factor
        db = get_db()
        db.execute(text("""
            INSERT INTO activities(category, amount, unit, note, kg_co2e)
            VALUES(:c,:a,:u,:n,:k)
        """), {"c": category, "a": amount, "u": unit, "n": note, "k": kg})
        db.commit()
        flash("Activity added.", "ok")
        return redirect(url_for("main.index"))
    categories = [
        ("electricity_nz","kWh"),
        ("car_gasoline","km"),
        ("natural_gas","kWh"),
        ("flight_shorthaul","km"),
        ("beef","kg"),
    ]
    return render_template("add_activity.html", categories=categories)

@bp.route("/list")
def list_activities():
    db = get_db()
    rows = db.execute(text("""
        SELECT id, ts, category, amount, unit, note, kg_co2e
        FROM activities ORDER BY ts DESC LIMIT 500
    """)).fetchall()
    return render_template("list.html", rows=rows)

@bp.route("/reports", methods=["GET","POST"])
def reports():
    db = get_db()
    if request.method == "POST":
        year = int(request.form["year"])
        month = int(request.form["month"])

        # Insert only if not exists
        existing = db.execute(text("""
            SELECT id, status FROM reports
            WHERE period_year=:y AND period_month=:m
        """), {"y": year, "m": month}).fetchone()

        if existing is None:
            db.execute(text("""
                INSERT INTO reports(period_year, period_month, status)
                VALUES(:y, :m, 'PENDING')
            """), {"y": year, "m": month})
            db.commit()
            flash("Report requested. It will be ready shortly.", "ok")
        else:
            flash("Report already exists for that month.", "info")

    reps = db.execute(text("""
        SELECT id, period_year, period_month, status, s3_key, created_at, updated_at
        FROM reports
        ORDER BY period_year DESC, period_month DESC
    """)).fetchall()

    # pass 'now' so the template can prefill
    return render_template("reports.html", reports=reps, now=datetime.utcnow)

# NEW: presigned download route (keeps bucket private)
@bp.route("/reports/<int:report_id>/download")
def download_report(report_id):
    db = get_db()
    row = db.execute(text("""
        SELECT status, s3_key
        FROM reports
        WHERE id = :id
    """), {"id": report_id}).fetchone()

    if not row or row["status"] != "COMPLETE" or not row["s3_key"]:
        abort(404)

    presigned = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": row["s3_key"]},
        ExpiresIn=3600  # 1 hour
    )
    return redirect(presigned)
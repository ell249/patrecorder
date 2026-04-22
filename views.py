import os
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, make_response
)
from sqlalchemy import or_, func
from weasyprint import HTML
from werkzeug.utils import secure_filename

from app import db
from config import Config
from models import Appliance, TestRecord, TestPhoto, RetestRule
from utils import fuzzy, get_suggested_interval, summarize_test_types, generate_qr_code

bp = Blueprint("main", __name__)

@bp.route("/")
def dashboard():
    recent_tests = TestRecord.query.order_by(TestRecord.test_date.desc()).limit(10).all()
    appliance_count = Appliance.query.count()
    test_count = TestRecord.query.count()
    return render_template("dashboard.html",
                           recent_tests=recent_tests,
                           appliance_count=appliance_count,
                           test_count=test_count)

@bp.route("/appliances")
def appliance_list():
    appliances = Appliance.query.order_by(Appliance.asset_number).all()
    return render_template("appliance_list.html", appliances=appliances)

@bp.route("/appliances/due")
def appliance_due():
    today = datetime.today().date()
    upcoming = today + timedelta(days=30)

    appliances = (
        db.session.query(Appliance)
        .join(TestRecord)
        .group_by(Appliance.id)
        .having(func.min(TestRecord.next_test_due) <= upcoming)
        .all()
    )

    return render_template("appliance_due.html", appliances=appliances)

@bp.route("/appliance/<int:appliance_id>")
def appliance_detail(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)
    test_summary = summarize_test_types(appliance.tests)
    return render_template("appliance_detail.html",
                           appliance=appliance,
                           test_summary=test_summary)

@bp.route("/test/<int:test_id>")
def test_detail(test_id):
    test = TestRecord.query.get_or_404(test_id)
    return render_template("test_detail.html", test=test)

@bp.route("/tests/new/<int:appliance_id>", methods=["GET", "POST"])
def new_test(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    if request.method == "POST":
        form = request.form
        files = request.files.getlist("photos")

        test_date = datetime.strptime(form["test_date"], "%Y-%m-%d")
        interval_days = int(form["retest_interval"])
        next_due = test_date + timedelta(days=interval_days)

        test = TestRecord(
            appliance_id=appliance.id,
            test_date=test_date,
            tester_name=form["tester_name"],
            test_type=form["test_type"],
            test_standard=form["test_standard"],
            tag_number=form["tag_number"],
            visual_pass=("visual_pass" in form),
            earth_continuity_ohms=form.get("earth_continuity_ohms") or None,
            insulation_mohms=form.get("insulation_mohms") or None,
            polarity_pass=("polarity_pass" in form) if "polarity_pass" in form else None,
            leakage_mA=form.get("leakage_mA") or None,
            overall_result=form["overall_result"],
            next_test_due=next_due.date(),
            comments=form.get("comments"),

            condition_assessment=form.get("condition_assessment"),
            functional_check=form.get("functional_check"),
            accessories=form.get("accessories"),
            safe_for_resale=form.get("safe_for_resale"),

            repair_description=form.get("repair_description"),
            repaired_by=form.get("repaired_by"),
            parts_replaced=form.get("parts_replaced"),
            post_repair_test=form.get("post_repair_test"),
        )

        db.session.add(test)
        db.session.commit()

        upload_dir = os.path.join(Config.UPLOAD_FOLDER, str(test.id))
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if not file or file.filename == "":
                continue
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            rel_path = f"tests/{test.id}/{filename}"
            photo = TestPhoto(
                test_id=test.id,
                filename=filename,
                filepath=rel_path
            )
            db.session.add(photo)

        db.session.commit()
        flash("Test record saved.", "success")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id))

    rules = RetestRule.query.order_by(RetestRule.interval_days).all()
    suggested_rule = get_suggested_interval(appliance.class_type or "ANY",
                                            appliance.supply_type or "ANY")

    return render_template("test_form.html",
                           appliance=appliance,
                           rules=rules,
                           suggested_rule=suggested_rule)

@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("main.appliance_list"))

    fq = fuzzy(q)

    appliances = Appliance.query.filter(
        or_(
            Appliance.asset_number.ilike(fq),
            Appliance.description.ilike(fq),
            Appliance.location.ilike(fq),
            Appliance.owner.ilike(fq),
        )
    ).all()

    tests = TestRecord.query.filter(
        TestRecord.tag_number.ilike(fq)
    ).all()

    return render_template("search_results.html",
                           q=q,
                           appliances=appliances,
                           tests=tests)

@bp.route("/test/<int:test_id>/pdf")
def test_pdf(test_id):
    test = TestRecord.query.get_or_404(test_id)
    appliance = test.appliance

    record_url = url_for("main.test_detail", test_id=test.id, _external=True)
    qr_code = generate_qr_code(record_url)

    if test.test_standard == "5761":
        template = "pdf/test_5761.html"
    elif test.test_standard == "5762":
        template = "pdf/test_5762.html"
    else:
        template = "pdf/test_3760.html"

    html = render_template(template, test=test, appliance=appliance, qr_code=qr_code)
    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=test_{test.id}.pdf"
    return response

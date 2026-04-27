import os
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, make_response
)
from sqlalchemy import or_
from weasyprint import HTML
from werkzeug.utils import secure_filename

from app import db
from config import Config
from models import Appliance, TestRecord, TestPhoto, RetestRule, Tester
from utils import (
    fuzzy,
    get_suggested_interval,
    summarize_test_types,
    generate_qr_code
)

bp = Blueprint("main", __name__)

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@bp.route("/")
def dashboard():
    today = datetime.today().date()
    soon = today + timedelta(days=30)

    never_tested = (
        Appliance.query
        .filter(Appliance.disposed == False)
        .filter(~Appliance.tests.any())
        .all()
    )

    due_tests = (
        Appliance.query
        .join(TestRecord)
        .filter(
            Appliance.disposed == False,
            TestRecord.disposed == False,
            TestRecord.next_test_due != None,
            TestRecord.next_test_due <= soon
        )
        .all()
    )

    due_appliances = {a.id: a for a in (never_tested + due_tests)}.values()

    upcoming_count = (
        Appliance.query
        .join(TestRecord)
        .filter(
            Appliance.disposed == False,
            TestRecord.disposed == False,
            TestRecord.next_test_due != None,
            TestRecord.next_test_due > today,
            TestRecord.next_test_due <= soon
        )
        .distinct()
        .count()
    )

    recent_tests = (
        TestRecord.query.filter_by(disposed=False)
        .order_by(TestRecord.test_date.desc())
        .limit(10)
        .all()
    )

    appliance_count = Appliance.query.filter_by(disposed=False).count()

    return render_template(
        "dashboard.html",
        recent_tests=recent_tests,
        appliance_count=appliance_count,
        due_appliances=due_appliances,
        upcoming_count=upcoming_count
    )

# ---------------------------------------------------------
# Appliance List
# ---------------------------------------------------------

@bp.route("/appliances")
def appliance_list():
    show_disposed = request.args.get("show_disposed") == "1"

    if show_disposed:
        appliances = Appliance.query.order_by(Appliance.asset_number).all()
    else:
        appliances = (
            Appliance.query.filter_by(disposed=False)
            .order_by(Appliance.asset_number)
            .all()
        )

    return render_template(
        "appliance_list.html",
        appliances=appliances,
        show_disposed=show_disposed
    )

# ---------------------------------------------------------
# Add Appliance
# ---------------------------------------------------------

@bp.route("/appliances/new", methods=["GET", "POST"])
def new_appliance():
    if request.method == "POST":
        form = request.form

        asset_number = form["asset_number"]

        existing = Appliance.query.filter_by(asset_number=asset_number).first()
        if existing:
            suffix = 1
            while True:
                candidate = f"{asset_number}-{suffix}"
                if not Appliance.query.filter_by(asset_number=candidate).first():
                    asset_number = candidate
                    break
                suffix += 1

        appliance = Appliance(
            asset_number=asset_number,
            description=form.get("description"),
            make_model=form.get("make_model"),
            location=form.get("location"),
            owner=form.get("owner"),
            class_type=form.get("class_type"),
            supply_type=form.get("supply_type"),
        )

        db.session.add(appliance)
        db.session.commit()

        flash("Appliance added successfully.", "success")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id))

    return render_template("appliance_form.html")

# ---------------------------------------------------------
# Edit Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/edit", methods=["GET", "POST"])
def edit_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    if request.method == "POST":
        form = request.form

        appliance.asset_number = form["asset_number"]
        appliance.description = form.get("description")
        appliance.make_model = form.get("make_model")
        appliance.location = form.get("location")
        appliance.owner = form.get("owner")
        appliance.class_type = form.get("class_type")
        appliance.supply_type = form.get("supply_type")

        db.session.commit()

        flash("Appliance updated successfully.", "success")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id))

    return render_template(
        "appliance_form.html",
        appliance=appliance,
        edit_mode=True
    )

# ---------------------------------------------------------
# Dispose Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/dispose", methods=["POST"])
def dispose_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    appliance.disposed = True
    for test in appliance.tests:
        test.disposed = True

    db.session.commit()

    flash("Appliance has been marked as disposed.", "warning")
    return redirect(url_for("main.appliance_list"))

# ---------------------------------------------------------
# Restore Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/restore", methods=["POST"])
def restore_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    appliance.disposed = False
    for test in appliance.tests:
        test.disposed = False

    db.session.commit()

    flash("Appliance has been restored.", "success")
    return redirect(url_for("main.edit_appliance", appliance_id=appliance.id))

# ---------------------------------------------------------
# Delete Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/delete", methods=["POST"])
def delete_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    for test in appliance.tests:
        for photo in test.photos:
            db.session.delete(photo)
        db.session.delete(test)

    db.session.delete(appliance)
    db.session.commit()

    flash("Appliance and all associated tests have been permanently deleted.", "success")
    return redirect(url_for("main.appliance_list"))

# ---------------------------------------------------------
# Appliance Detail
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>")
def appliance_detail(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    test_summary = summarize_test_types(
        [t for t in appliance.tests if not t.disposed]
    )

    return render_template(
        "appliance_detail.html",
        appliance=appliance,
        test_summary=test_summary
    )

# ---------------------------------------------------------
# Test Detail
# ---------------------------------------------------------

@bp.route("/test/<int:test_id>")
def test_detail(test_id):
    test = TestRecord.query.get_or_404(test_id)
    return render_template("test_detail.html", test=test)

# ---------------------------------------------------------
# Add Test
# ---------------------------------------------------------

@bp.route("/tests/new/<int:appliance_id>", methods=["GET", "POST"])
def new_test(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    if request.method == "POST":
        form = request.form
        files = request.files.getlist("photos")

        test_date = datetime.strptime(form["test_date"], "%Y-%m-%d")
        interval_days = int(form["retest_interval"])
        next_due = test_date + timedelta(days=interval_days)

        tester_id = int(form["tester_id"])
        tester = Tester.query.get(tester_id)

        def bool_from_dropdown(value):
            return value == "PASS"

        test = TestRecord(
            appliance_id=appliance.id,
            tester_id=tester.id,
            test_date=test_date,
            test_type=form["test_type"],
            test_standard=form["test_standard"],
            tag_number=form["tag_number"],
            next_test_due=next_due.date(),
            overall_result=form["overall_result"],
            comments=form.get("comments"),

            # Visual inspection
            vi_plug=bool_from_dropdown(form.get("vi_plug")),
            vi_cord=bool_from_dropdown(form.get("vi_cord")),
            vi_casing=bool_from_dropdown(form.get("vi_casing")),
            vi_overheat=bool_from_dropdown(form.get("vi_overheat")),
            vi_label=bool_from_dropdown(form.get("vi_label")),
            vi_exposed=bool_from_dropdown(form.get("vi_exposed")),

            vi_repairs=form.get("vi_repairs"),
            vi_strain=form.get("vi_strain"),
            vi_guards=form.get("vi_guards"),

            # Electrical tests
            earth_continuity_ohms=form.get("earth_continuity_ohms") or None,
            insulation_mohms=form.get("insulation_mohms") or None,
            leakage_mA=form.get("leakage_mA") or None,
            polarity_pass=("polarity_pass" in form),

            # 5761 / 5762
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

        # Handle photos
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

    # GET request
    testers = Tester.query.order_by(Tester.full_name).all()
    rules = RetestRule.query.order_by(RetestRule.interval_days).all()
    suggested_rule = get_suggested_interval(
        appliance.class_type or "ANY",
        appliance.supply_type or "ANY"
    )

    return render_template(
        "test_form.html",
        appliance=appliance,
        testers=testers,
        rules=rules,
        suggested_rule=suggested_rule
    )

# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

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
            Appliance.make_model.ilike(fq),
            Appliance.location.ilike(fq),
            Appliance.owner.ilike(fq),
        )
    ).all()

    tests = TestRecord.query.filter(
        TestRecord.tag_number.ilike(fq)
    ).all()

    return render_template(
        "search_results.html",
        q=q,
        appliances=appliances,
        tests=tests
    )

# ---------------------------------------------------------
# PDF Export
# ---------------------------------------------------------

@bp.route("/test/<int:test_id>/pdf")
def test_pdf(test_id):
    test = TestRecord.query.get_or_404(test_id)
    appliance = test.appliance
    tester = test.tester

    record_url = url_for("main.test_detail", test_id=test.id, _external=True)
    qr_code = generate_qr_code(record_url)

    if test.test_standard == "5761":
        template = "pdf/test_5761.html"
    elif test.test_standard == "5762":
        template = "pdf/test_5762.html"
    else:
        template = "pdf/test_3760.html"

    html = render_template(
        template,
        test=test,
        appliance=appliance,
        tester=tester,
        qr_code=qr_code
    )

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=test_{test.id}.pdf"
    return response

# ---------------------------------------------------------
# Add Tester
# ---------------------------------------------------------

@bp.route("/testers/new/modal", methods=["POST"])
def new_tester_modal():
    full_name = request.form["full_name"]
    cert = request.form["certificate_number"]
    phone = request.form.get("phone")
    appliance_id = request.form.get("appliance_id")

    tester = Tester(full_name=full_name, certificate_number=cert, phone_number=phone)
    db.session.add(tester)
    db.session.commit()

    # Return to the test form
    return redirect(url_for("main.new_test", appliance_id=appliance_id))

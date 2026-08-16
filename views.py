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
from models import Appliance, TestRecord, TestPhoto, RetestRule, Tester, RepairRecord, RepairPhoto, ApplianceDocument
from utils import (
    make_snippet,
    fuzzy,
    get_suggested_interval,
    summarize_test_types,
    generate_qr_code
)

bp = Blueprint("main", __name__)


def _auto_tag(appliance):
    prefix = appliance.asset_number
    existing = {t.tag_number for t in appliance.tests}
    seq = 1
    while f"{prefix}-{seq}" in existing:
        seq += 1
    return f"{prefix}-{seq}"

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@bp.route("/")
def dashboard():
    today = datetime.today().date()
    soon = today + timedelta(days=30)

    # Non-NTS appliances with no tests
    never_tested = (
        Appliance.query
        .filter(Appliance.disposed == False, Appliance.new_to_service != True)
        .filter(~Appliance.tests.any())
        .all()
    )

    # NTS appliances with no tests — split by whether the interval has elapsed
    nts_untested = (
        Appliance.query
        .filter(Appliance.disposed == False, Appliance.new_to_service == True)
        .filter(~Appliance.tests.any())
        .all()
    )
    nts_not_yet_due, nts_now_due = [], []
    for _a in nts_untested:
        _due = _a.nts_next_test_due
        if _due and _due > today:
            nts_not_yet_due.append(_a)
        else:
            nts_now_due.append(_a)

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

    # Appliances with open (unlinked/unlocked) repair records
    repaired_needs_test = (
        Appliance.query
        .filter(Appliance.disposed == False)
        .filter(Appliance.repairs.any(
            (RepairRecord.disposed == False) &
            (RepairRecord.locked_by_test_date == None)
        ))
        .all()
    )

    # Build merged due list with reason labels; de-duplicate by appliance id
    reason_map = {}
    for a in never_tested:
        reason_map[a.id] = "Never tested"
    for a in due_tests:
        reason_map.setdefault(a.id, "Overdue")
    for a in repaired_needs_test:
        reason_map[a.id] = "Repaired – test required"
    for a in nts_now_due:
        reason_map[a.id] = "NTS period elapsed – test required"

    due_appliances_map = {a.id: a for a in (never_tested + due_tests + repaired_needs_test + nts_now_due)}
    due_appliances = due_appliances_map.values()

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

    from flask import current_app
    recent_limit = int(current_app.config.get('DASHBOARD_RECENT_LIMIT', 5))

    recent_tests = (
        TestRecord.query.filter_by(disposed=False)
        .order_by(TestRecord.test_date.desc(), TestRecord.id.desc())
        .limit(recent_limit)
        .all()
    )

    recent_repairs = (
        RepairRecord.query.filter_by(disposed=False)
        .order_by(RepairRecord.repair_date.desc(), RepairRecord.id.desc())
        .limit(recent_limit)
        .all()
    )

    appliance_count = Appliance.query.filter_by(disposed=False).count()

    required_count = len(due_appliances_map)

    return render_template(
        "dashboard.html",
        recent_tests=recent_tests,
        appliance_count=appliance_count,
        due_appliances=due_appliances,
        upcoming_count=upcoming_count,
        required_count=required_count,
        reason_map=reason_map,
        nts_not_yet_due=nts_not_yet_due,
        recent_repairs=recent_repairs,
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

        purchase_date_str = form.get("purchase_date")
        purchase_price_str = form.get("purchase_price")

        entry_date_str = form.get("entry_to_service_date")
        interval_raw   = form.get("default_retest_interval_days")

        appliance = Appliance(
            asset_number=asset_number,
            description=form.get("description"),
            make_model=form.get("make_model"),
            location=form.get("location"),
            owner=form.get("owner"),
            class_type=form.get("class_type"),
            supply_type=form.get("supply_type"),
            serial_number=form.get("serial_number") or None,
            purchase_date=datetime.strptime(purchase_date_str, "%Y-%m-%d").date() if purchase_date_str else None,
            purchase_price=float(purchase_price_str) if purchase_price_str else None,
            new_to_service=bool(form.get("new_to_service")),
            entry_to_service_date=datetime.strptime(entry_date_str, "%Y-%m-%d").date() if entry_date_str else None,
            default_retest_interval_days=int(interval_raw) if interval_raw else None,
        )

        db.session.add(appliance)
        db.session.commit()

        files = request.files.getlist("documents")
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                doc_dir = os.path.join("static", "uploads", "receipts", str(appliance.id))
                os.makedirs(doc_dir, exist_ok=True)
                f.save(os.path.join(doc_dir, filename))
                db.session.add(ApplianceDocument(
                    appliance_id=appliance.id,
                    filename=filename,
                    filepath=f"receipts/{appliance.id}/{filename}",
                ))
        db.session.commit()

        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id, just_created=1))

    return render_template("appliance_form.html")

# ---------------------------------------------------------
# Edit Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/edit", methods=["GET", "POST"])
def edit_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    if request.method == "POST":
        form = request.form

        purchase_date_str = form.get("purchase_date")
        purchase_price_str = form.get("purchase_price")

        entry_date_str = form.get("entry_to_service_date")
        interval_raw   = form.get("default_retest_interval_days")

        appliance.asset_number = form["asset_number"]
        appliance.description = form.get("description")
        appliance.make_model = form.get("make_model")
        appliance.location = form.get("location")
        appliance.owner = form.get("owner")
        appliance.class_type = form.get("class_type")
        appliance.supply_type = form.get("supply_type")
        appliance.serial_number = form.get("serial_number") or None
        appliance.purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date() if purchase_date_str else None
        appliance.purchase_price = float(purchase_price_str) if purchase_price_str else None
        appliance.new_to_service = bool(form.get("new_to_service"))
        appliance.entry_to_service_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date() if entry_date_str else None
        appliance.default_retest_interval_days = int(interval_raw) if interval_raw else None

        files = request.files.getlist("documents")
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                doc_dir = os.path.join("static", "uploads", "receipts", str(appliance.id))
                os.makedirs(doc_dir, exist_ok=True)
                f.save(os.path.join(doc_dir, filename))
                db.session.add(ApplianceDocument(
                    appliance_id=appliance.id,
                    filename=filename,
                    filepath=f"receipts/{appliance.id}/{filename}",
                ))

        db.session.commit()

        flash("Appliance updated successfully.", "success")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id))

    return render_template(
        "appliance_form.html",
        appliance=appliance,
        edit_mode=True
    )

# ---------------------------------------------------------
# Delete Appliance Document
# ---------------------------------------------------------

@bp.route("/appliance-document/<int:doc_id>/delete", methods=["POST"])
def delete_appliance_document(doc_id):
    doc = ApplianceDocument.query.get_or_404(doc_id)
    appliance_id = doc.appliance_id
    path = os.path.join("static", "uploads", doc.filepath)
    if os.path.isfile(path):
        os.remove(path)
    db.session.delete(doc)
    db.session.commit()
    return redirect(url_for("main.appliance_detail", appliance_id=appliance_id))

# ---------------------------------------------------------
# Dispose Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/dispose", methods=["POST"])
def dispose_appliance(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    disposal_date_str = request.form.get("disposal_date")
    disposal_price_str = request.form.get("disposal_price")

    appliance.disposed = True
    appliance.disposal_date = datetime.strptime(disposal_date_str, "%Y-%m-%d").date() if disposal_date_str else None
    appliance.disposal_price = float(disposal_price_str) if disposal_price_str else None
    appliance.disposal_comment = request.form.get("disposal_comment") or None

    for test in appliance.tests:
        test.disposed = True
    for repair in appliance.repairs:
        repair.disposed = True

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
    for repair in appliance.repairs:
        repair.disposed = False

    db.session.commit()

    flash("Appliance has been restored.", "success")
    return redirect(url_for("main.edit_appliance", appliance_id=appliance.id))

# ---------------------------------------------------------
# Delete Appliance
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/delete", methods=["POST"])
def delete_appliance(appliance_id):
    import shutil
    appliance = Appliance.query.get_or_404(appliance_id)

    for test in appliance.tests:
        test_dir = os.path.join(Config.UPLOAD_FOLDER, str(test.id))
        if os.path.isdir(test_dir):
            shutil.rmtree(test_dir)
        for photo in test.photos:
            db.session.delete(photo)
        db.session.delete(test)

    for repair in appliance.repairs:
        repair_dir = os.path.join("static", "uploads", "repairs", str(repair.id))
        if os.path.isdir(repair_dir):
            shutil.rmtree(repair_dir)

    receipt_dir = os.path.join("static", "uploads", "receipts", str(appliance.id))
    if os.path.isdir(receipt_dir):
        shutil.rmtree(receipt_dir)

    db.session.delete(appliance)
    db.session.commit()

    flash("Appliance and all associated records have been permanently deleted.", "success")
    return redirect(url_for("main.appliance_list"))

# ---------------------------------------------------------
# Appliance Detail
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>")
def appliance_detail(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    active_tests = sorted(
        [t for t in appliance.tests if not t.disposed],
        key=lambda t: (t.test_date, t.id),
        reverse=True,
    )
    active_repairs = sorted(
        [r for r in appliance.repairs if not r.disposed],
        key=lambda r: (r.repair_date, r.id),
        reverse=True,
    )

    test_summary = summarize_test_types(active_tests)

    return render_template(
        "appliance_detail.html",
        appliance=appliance,
        active_tests=active_tests,
        active_repairs=active_repairs,
        test_summary=test_summary,
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
        next_due = (test_date + timedelta(days=interval_days)) if interval_days else None

        tester_id = int(form["tester_id"])
        tester = Tester.query.get(tester_id)

        def bool_from_dropdown(value):
            if value == "PASS":
                return True
            elif value == "FAIL":
                return False
            return None  # N/A or not answered

        test = TestRecord(
            appliance_id=appliance.id,
            tester_id=tester.id,
            test_date=test_date,
            test_type=form["test_type"],
            test_standard=form["test_standard"],
            tag_number=form.get("tag_number").strip() or _auto_tag(appliance),
            next_test_due=next_due.date() if next_due else None,
            overall_result=form["overall_result"],
            comments=form.get("comments"),

            # Visual inspection
            vi_plug=bool_from_dropdown(form.get("vi_plug")),
            vi_cord=bool_from_dropdown(form.get("vi_cord")),
            vi_casing=form.get("vi_casing") or None,
            vi_overheat=bool_from_dropdown(form.get("vi_overheat")),
            vi_label=form.get("vi_label") or None,
            vi_exposed=bool_from_dropdown(form.get("vi_exposed")),

            vi_repairs=form.get("vi_repairs"),
            vi_strain=form.get("vi_strain"),
            vi_guards=form.get("vi_guards"),

            # Electrical tests — all N/A for Battery/ELV (section is hidden in the form)
            earth_continuity_ohms="N/A" if appliance.class_type in ("CLASS II", "BATTERY_ELV") else (form.get("earth_continuity_ohms") or None),
            insulation_mohms="N/A" if appliance.class_type == "BATTERY_ELV" else (form.get("insulation_mohms") or None),
            leakage_mA="N/A" if appliance.class_type == "BATTERY_ELV" else (form.get("leakage_mA") or None),
            polarity_pass="N/A" if appliance.class_type == "BATTERY_ELV" else (form.get("polarity_pass") or None),

            # 5761
            condition_assessment=form.get("condition_assessment"),
            functional_check=form.get("functional_check"),
            accessories=form.get("accessories"),
            safe_for_resale=form.get("safe_for_resale"),
            no_outstanding_recalls=form.get("no_outstanding_recalls") or None,
            pins_insulated=form.get("pins_insulated") or None,

            # 5762 — functional tests
            func_test_1_method=form.get("func_test_1_method") or None,
            func_test_1_result=form.get("func_test_1_result") or None,
            func_test_2_method=form.get("func_test_2_method") or None,
            func_test_2_result=form.get("func_test_2_result") or None,
            func_test_3_method=form.get("func_test_3_method") or None,
            func_test_3_result=form.get("func_test_3_result") or None,
            func_test_4_method=form.get("func_test_4_method") or None,
            func_test_4_result=form.get("func_test_4_result") or None,
            func_test_5_method=form.get("func_test_5_method") or None,
            func_test_5_result=form.get("func_test_5_result") or None,
        )

        db.session.add(test)
        db.session.flush()  # get test.id before linking repairs

        # 5762 — link selected repair records (many-to-many)
        selected_repair_ids = [int(x) for x in form.getlist("linked_repair_ids") if x.isdigit()]
        if selected_repair_ids:
            test.linked_repairs = RepairRecord.query.filter(
                RepairRecord.id.in_(selected_repair_ids)
            ).all()

        # Lock any repair records explicitly linked to this test
        for repair in test.linked_repairs:
            repair.locked_by_test_date = test_date.date()
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
    unlocked_repairs = (
        RepairRecord.query
        .filter_by(appliance_id=appliance.id, disposed=False)
        .filter(RepairRecord.locked_by_test_date == None)
        .order_by(RepairRecord.repair_date.desc())
        .all()
    )

    return render_template(
        "test_form.html",
        appliance=appliance,
        testers=testers,
        rules=rules,
        suggested_rule=suggested_rule,
        unlocked_repairs=unlocked_repairs,
    )

# ---------------------------------------------------------
# Repair helpers
# ---------------------------------------------------------

# ---------------------------------------------------------
# Add Repair
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/repairs/new", methods=["GET", "POST"])
def new_repair(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)

    if request.method == "POST":
        form = request.form
        files = request.files.getlist("photos")

        repair_date = datetime.strptime(form["repair_date"], "%Y-%m-%d").date()

        parts_cost_raw = form.get("parts_cost", "").strip()
        parts_cost = float(parts_cost_raw) if parts_cost_raw else None

        labour_time_raw = form.get("labour_time", "").strip()
        labour_minutes = None
        if labour_time_raw:
            parts = labour_time_raw.split(":")
            labour_minutes = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else None

        repair = RepairRecord(
            appliance_id=appliance.id,
            repair_date=repair_date,
            repaired_by=form.get("repaired_by") or None,
            description=form["description"],
            comments=form.get("comments") or None,
            parts_cost=parts_cost,
            labour_minutes=labour_minutes,
        )
        db.session.add(repair)
        db.session.commit()

        upload_dir = os.path.join("static", "uploads", "repairs", str(repair.id))
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if not file or file.filename == "":
                continue
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_dir, filename))
            rel_path = f"repairs/{repair.id}/{filename}"
            db.session.add(RepairPhoto(repair_id=repair.id, filename=filename, filepath=rel_path))

        db.session.commit()

        flash("Repair record saved.", "success")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance.id))

    return render_template("repair_form.html", appliance=appliance)


# ---------------------------------------------------------
# Repair Detail
# ---------------------------------------------------------

@bp.route("/repair/<int:repair_id>")
def repair_detail(repair_id):
    repair = RepairRecord.query.get_or_404(repair_id)
    return render_template("repair_detail.html", repair=repair)


# ---------------------------------------------------------
# Edit Repair
# ---------------------------------------------------------

@bp.route("/repair/<int:repair_id>/edit", methods=["GET", "POST"])
def edit_repair(repair_id):
    repair = RepairRecord.query.get_or_404(repair_id)

    if repair.locked_by_test_date:
        flash(f"This repair is locked — a test was conducted on {repair.locked_by_test_date.strftime('%d/%m/%Y')}.", "warning")
        return redirect(url_for("main.repair_detail", repair_id=repair.id))

    if request.method == "POST":
        form = request.form
        files = request.files.getlist("photos")

        repair.repair_date = datetime.strptime(form["repair_date"], "%Y-%m-%d").date()
        repair.repaired_by = form.get("repaired_by") or None
        repair.description = form["description"]
        repair.comments = form.get("comments") or None

        parts_cost_raw = form.get("parts_cost", "").strip()
        repair.parts_cost = float(parts_cost_raw) if parts_cost_raw else None

        labour_time_raw = form.get("labour_time", "").strip()
        if labour_time_raw:
            parts = labour_time_raw.split(":")
            repair.labour_minutes = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else None
        else:
            repair.labour_minutes = None

        db.session.commit()

        upload_dir = os.path.join("static", "uploads", "repairs", str(repair.id))
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if not file or file.filename == "":
                continue
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_dir, filename))
            rel_path = f"repairs/{repair.id}/{filename}"
            db.session.add(RepairPhoto(repair_id=repair.id, filename=filename, filepath=rel_path))

        db.session.commit()

        flash("Repair record updated.", "success")
        return redirect(url_for("main.repair_detail", repair_id=repair.id))

    return render_template("repair_form.html", appliance=repair.appliance, repair=repair)


# ---------------------------------------------------------
# Delete Repair
# ---------------------------------------------------------

@bp.route("/repair/<int:repair_id>/delete", methods=["POST"])
def delete_repair(repair_id):
    repair = RepairRecord.query.get_or_404(repair_id)
    appliance_id = repair.appliance_id

    if repair.locked_by_test_date:
        flash("Locked repair records cannot be deleted.", "danger")
        return redirect(url_for("main.repair_detail", repair_id=repair.id))

    upload_dir = os.path.join("static", "uploads", "repairs", str(repair.id))
    if os.path.isdir(upload_dir):
        import shutil
        shutil.rmtree(upload_dir)

    db.session.delete(repair)
    db.session.commit()

    flash("Repair record deleted.", "success")
    return redirect(url_for("main.appliance_detail", appliance_id=appliance_id))


# ---------------------------------------------------------
# Repair History PDF
# ---------------------------------------------------------

@bp.route("/appliance/<int:appliance_id>/repairs/pdf")
def repair_history_pdf(appliance_id):
    appliance = Appliance.query.get_or_404(appliance_id)
    repairs = (
        RepairRecord.query
        .filter_by(appliance_id=appliance_id, disposed=False)
        .order_by(RepairRecord.repair_date)
        .all()
    )

    appliance_url = url_for("main.appliance_detail", appliance_id=appliance.id, _external=True)
    qr_code = generate_qr_code(appliance_url)

    html = render_template(
        "pdf/repair_history.html",
        appliance=appliance,
        repairs=repairs,
        qr_code=qr_code,
        now=datetime.today()
    )

    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=repairs_{appliance_id}.pdf"
    return response


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("main.appliance_list"))

    fq = fuzzy(q)

    appliances = Appliance.query.filter(
        Appliance.disposed == False,
        or_(
            Appliance.asset_number.ilike(fq),
            Appliance.description.ilike(fq),
            Appliance.make_model.ilike(fq),
            Appliance.serial_number.ilike(fq),
            Appliance.location.ilike(fq),
            Appliance.owner.ilike(fq),
        )
    ).order_by(Appliance.asset_number).all()

    raw_tests = TestRecord.query.filter(
        TestRecord.disposed == False,
        or_(
            TestRecord.tag_number.ilike(fq),
            TestRecord.comments.ilike(fq),
            TestRecord.repair_description.ilike(fq),
            TestRecord.repaired_by.ilike(fq),
        )
    ).order_by(TestRecord.test_date.desc()).all()

    raw_repairs = RepairRecord.query.filter(
        RepairRecord.disposed == False,
        or_(
            RepairRecord.description.ilike(fq),
            RepairRecord.comments.ilike(fq),
            RepairRecord.repaired_by.ilike(fq),
        )
    ).order_by(RepairRecord.repair_date.desc()).all()

    def first_match(record, fields):
        for label, attr in fields:
            val = getattr(record, attr, None) or ''
            if q.lower() in val.lower():
                return label, make_snippet(val, q)
        return '', ''

    test_results = [
        {'test': t, **dict(zip(('field', 'snippet'), first_match(t, [
            ('Comment', 'comments'),
            ('Repair description', 'repair_description'),
            ('Repaired by', 'repaired_by'),
            ('Tag', 'tag_number'),
        ])))}
        for t in raw_tests
    ]

    repair_results = [
        {'repair': r, **dict(zip(('field', 'snippet'), first_match(r, [
            ('Description', 'description'),
            ('Comment', 'comments'),
            ('Repaired by', 'repaired_by'),
        ])))}
        for r in raw_repairs
    ]

    return render_template(
        "search_results.html",
        q=q,
        appliances=appliances,
        test_results=test_results,
        repair_results=repair_results,
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
    elif test.test_standard in ("5762", "VISUAL"):
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
# Label Print / Preview
# ---------------------------------------------------------

@bp.route("/test/<int:test_id>/label")
def test_label(test_id):
    from flask import current_app
    from label import build_label_image, print_label

    test = TestRecord.query.get_or_404(test_id)
    config = {
        "BASE_URL":        current_app.config.get("BASE_URL", ""),
        "BROTHER_PRINTER": current_app.config.get("BROTHER_PRINTER", ""),
        "BROTHER_MODEL":   current_app.config.get("BROTHER_MODEL", "QL-810W"),
        "BROTHER_LABEL":   current_app.config.get("BROTHER_LABEL", "62"),
        "BROTHER_RED":     current_app.config.get("BROTHER_RED", "false"),
    }

    if not config["BROTHER_PRINTER"]:
        flash("No printer configured. Set a printer address in Printer Settings.", "warning")
        return redirect(url_for("main.test_detail", test_id=test_id))

    try:
        img_bytes = build_label_image(test, config)
        print_label(img_bytes, config)
        flash("Label sent to printer.", "success")
    except Exception as exc:
        flash(f"Print failed: {exc}", "danger")

    return redirect(url_for("main.test_detail", test_id=test_id))


@bp.route("/test/<int:test_id>/label/preview")
def test_label_preview(test_id):
    from flask import current_app
    from label import build_label_image

    test = TestRecord.query.get_or_404(test_id)
    config = {
        "BASE_URL":    current_app.config.get("BASE_URL", ""),
        "BROTHER_RED": current_app.config.get("BROTHER_RED", "false"),
    }
    img_bytes = build_label_image(test, config)
    response = make_response(img_bytes)
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.route("/appliance/<int:appliance_id>/nts-label")
def nts_label(appliance_id):
    from flask import current_app
    from label import build_nts_label_image, print_label

    appliance = Appliance.query.get_or_404(appliance_id)
    if not appliance.new_to_service:
        flash("This appliance is not flagged as New to Service.", "warning")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance_id))

    config = {
        "BASE_URL":        current_app.config.get("BASE_URL", ""),
        "BROTHER_PRINTER": current_app.config.get("BROTHER_PRINTER", ""),
        "BROTHER_MODEL":   current_app.config.get("BROTHER_MODEL", "QL-810W"),
        "BROTHER_LABEL":   current_app.config.get("BROTHER_LABEL", "62"),
        "BROTHER_RED":     current_app.config.get("BROTHER_RED", "false"),
    }
    if not config["BROTHER_PRINTER"]:
        flash("No printer configured. Set a printer address in Printer Settings.", "warning")
        return redirect(url_for("main.appliance_detail", appliance_id=appliance_id))

    try:
        img_bytes = build_nts_label_image(appliance, config)
        print_label(img_bytes, config)
        flash("NTS label sent to printer.", "success")
    except Exception as exc:
        flash(f"Print failed: {exc}", "danger")

    return redirect(url_for("main.appliance_detail", appliance_id=appliance_id))


@bp.route("/appliance/<int:appliance_id>/nts-label/preview")
def nts_label_preview(appliance_id):
    from flask import current_app
    from label import build_nts_label_image

    appliance = Appliance.query.get_or_404(appliance_id)
    config = {"BASE_URL": current_app.config.get("BASE_URL", "")}
    img_bytes = build_nts_label_image(appliance, config)
    response = make_response(img_bytes)
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "no-store"
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

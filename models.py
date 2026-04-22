from app import db
from datetime import datetime


class Appliance(db.Model):
    __tablename__ = "appliance"

    id = db.Column(db.Integer, primary_key=True)
    asset_number = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255))
    make_model = db.Column(db.String(255))
    location = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    class_type = db.Column(db.String(50))
    supply_type = db.Column(db.String(50))

    disposed = db.Column(db.Boolean, default=False)

    tests = db.relationship("TestRecord", backref="appliance", lazy=True)

    def __repr__(self):
        return f"<Appliance {self.asset_number}>"


class TestRecord(db.Model):
    __tablename__ = "test_record"

    id = db.Column(db.Integer, primary_key=True)
    appliance_id = db.Column(db.Integer, db.ForeignKey("appliance.id"), nullable=False)

    test_date = db.Column(db.Date, nullable=False)
    tester_name = db.Column(db.String(255), nullable=False)
    test_type = db.Column(db.String(255), nullable=False)
    test_standard = db.Column(db.String(50), nullable=False)
    tag_number = db.Column(db.String(255), nullable=False)

    # -------------------------------
    # Visual Inspection Fields
    # -------------------------------

    # Simple PASS/FAIL items (boolean)
    vi_plug = db.Column(db.Boolean)
    vi_cord = db.Column(db.Boolean)
    vi_casing = db.Column(db.Boolean)
    vi_overheat = db.Column(db.Boolean)
    vi_label = db.Column(db.Boolean)
    vi_exposed = db.Column(db.Boolean)

    # PASS / FAIL / N/A items (string)
    vi_repairs = db.Column(db.String(10))   # PASS / FAIL / N/A
    vi_strain = db.Column(db.String(10))    # PASS / FAIL / N/A
    vi_guards = db.Column(db.String(10))    # PASS / FAIL / N/A

    # -------------------------------
    # Electrical Test Fields
    # -------------------------------
    visual_pass = db.Column(db.Boolean)  # (legacy, can be removed later)
    earth_continuity_ohms = db.Column(db.String(50))
    insulation_mohms = db.Column(db.String(50))
    polarity_pass = db.Column(db.Boolean)
    leakage_mA = db.Column(db.String(50))

    overall_result = db.Column(db.String(10), nullable=False)
    next_test_due = db.Column(db.Date)
    comments = db.Column(db.Text)

    # -------------------------------
    # 5761 / 5762 Additional Fields
    # -------------------------------
    condition_assessment = db.Column(db.String(255))
    functional_check = db.Column(db.String(255))
    accessories = db.Column(db.String(255))
    safe_for_resale = db.Column(db.String(255))

    repair_description = db.Column(db.Text)
    repaired_by = db.Column(db.String(255))
    parts_replaced = db.Column(db.Text)
    post_repair_test = db.Column(db.String(255))

    disposed = db.Column(db.Boolean, default=False)

    photos = db.relationship("TestPhoto", backref="test", lazy=True)

    def __repr__(self):
        return f"<TestRecord {self.id}>"


class TestPhoto(db.Model):
    __tablename__ = "test_photo"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test_record.id"), nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<TestPhoto {self.filename}>"


class RetestRule(db.Model):
    __tablename__ = "retest_rule"

    id = db.Column(db.Integer, primary_key=True)
    class_type = db.Column(db.String(50))
    supply_type = db.Column(db.String(50))
    interval_days = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<RetestRule {self.class_type}/{self.supply_type}: {self.interval_days} days>"
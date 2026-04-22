from app import db
from datetime import datetime


class Appliance(db.Model):
    __tablename__ = "appliance"

    id = db.Column(db.Integer, primary_key=True)
    asset_number = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    make_model = db.Column(db.String(255))          # NEW FIELD
    location = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    class_type = db.Column(db.String(64))
    supply_type = db.Column(db.String(64))
    disposed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tests = db.relationship("TestRecord", backref="appliance", lazy=True)


class TestRecord(db.Model):
    __tablename__ = "test_record"

    id = db.Column(db.Integer, primary_key=True)
    appliance_id = db.Column(db.Integer, db.ForeignKey("appliance.id"))

    test_date = db.Column(db.DateTime)
    tester_name = db.Column(db.String(255))
    test_type = db.Column(db.String(255))
    test_standard = db.Column(db.String(32))
    tag_number = db.Column(db.String(64))

    visual_pass = db.Column(db.Boolean)
    earth_continuity_ohms = db.Column(db.String(64))
    insulation_mohms = db.Column(db.String(64))
    polarity_pass = db.Column(db.Boolean)
    leakage_mA = db.Column(db.String(64))

    overall_result = db.Column(db.String(16))
    next_test_due = db.Column(db.Date)
    comments = db.Column(db.Text)

    condition_assessment = db.Column(db.String(255))
    functional_check = db.Column(db.String(255))
    accessories = db.Column(db.String(255))
    safe_for_resale = db.Column(db.String(255))

    repair_description = db.Column(db.Text)
    repaired_by = db.Column(db.String(255))
    parts_replaced = db.Column(db.String(255))
    post_repair_test = db.Column(db.String(255))

    disposed = db.Column(db.Boolean, default=False)

    photos = db.relationship("TestPhoto", backref="test", lazy=True)


class TestPhoto(db.Model):
    __tablename__ = "test_photo"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test_record.id"))
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))


class RetestRule(db.Model):
    __tablename__ = "retest_rule"

    id = db.Column(db.Integer, primary_key=True)
    class_type = db.Column(db.String(64), nullable=False)
    supply_type = db.Column(db.String(64), nullable=False)
    interval_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    priority = db.Column(db.Integer, default=0)

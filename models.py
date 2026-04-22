from datetime import datetime
from app import db

class Appliance(db.Model):
    __tablename__ = "appliances"

    id = db.Column(db.Integer, primary_key=True)
    asset_number = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    location = db.Column(db.String(255))
    owner = db.Column(db.String(255))
    class_type = db.Column(db.String(32))
    supply_type = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tests = db.relationship("TestRecord", backref="appliance", lazy=True)


class TestRecord(db.Model):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)
    appliance_id = db.Column(db.Integer, db.ForeignKey("appliances.id"), nullable=False)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    tester_name = db.Column(db.String(255))
    test_type = db.Column(db.String(64))
    test_standard = db.Column(db.String(16), default="3760")
    tag_number = db.Column(db.String(64))

    visual_pass = db.Column(db.Boolean, default=False)
    earth_continuity_ohms = db.Column(db.Numeric(10, 3))
    insulation_mohms = db.Column(db.Numeric(10, 3))
    polarity_pass = db.Column(db.Boolean)
    leakage_mA = db.Column(db.Numeric(10, 3))

    overall_result = db.Column(db.String(16))
    next_test_due = db.Column(db.Date)
    comments = db.Column(db.Text)

    condition_assessment = db.Column(db.Text)
    functional_check = db.Column(db.Text)
    accessories = db.Column(db.String(255))
    safe_for_resale = db.Column(db.String(8))

    repair_description = db.Column(db.Text)
    repaired_by = db.Column(db.String(255))
    parts_replaced = db.Column(db.Text)
    post_repair_test = db.Column(db.Text)

    photos = db.relationship("TestPhoto", backref="test", lazy=True,
                             cascade="all, delete-orphan")


class TestPhoto(db.Model):
    __tablename__ = "test_photos"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class RetestRule(db.Model):
    __tablename__ = "retest_rules"

    id = db.Column(db.Integer, primary_key=True)
    class_type = db.Column(db.String(32))
    supply_type = db.Column(db.String(64))
    interval_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    priority = db.Column(db.Integer, default=0)

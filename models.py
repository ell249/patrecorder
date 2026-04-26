from app import db

# ---------------------------------------------------------
# Tester Table
# ---------------------------------------------------------
class Tester(db.Model):
    __tablename__ = "tester"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    certificate_number = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50))

    # Relationship: one tester → many test records
    tests = db.relationship("TestRecord", back_populates="tester")


# ---------------------------------------------------------
# Appliance Table
# ---------------------------------------------------------
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

    tests = db.relationship("TestRecord", back_populates="appliance")


# ---------------------------------------------------------
# Test Record Table
# ---------------------------------------------------------
class TestRecord(db.Model):
    __tablename__ = "test_record"

    id = db.Column(db.Integer, primary_key=True)

    appliance_id = db.Column(db.Integer, db.ForeignKey("appliance.id"), nullable=False)
    tester_id = db.Column(db.Integer, db.ForeignKey("tester.id"), nullable=False)

    test_date = db.Column(db.Date, nullable=False)
    test_type = db.Column(db.String(255), nullable=False)
    test_standard = db.Column(db.String(50), nullable=False)
    tag_number = db.Column(db.String(255), nullable=False)

    next_test_due = db.Column(db.Date)
    overall_result = db.Column(db.String(10), nullable=False)
    comments = db.Column(db.Text)
    disposed = db.Column(db.Boolean, default=False)

    # Visual inspection (booleans)
    vi_plug = db.Column(db.Boolean)
    vi_cord = db.Column(db.Boolean)
    vi_casing = db.Column(db.Boolean)
    vi_overheat = db.Column(db.Boolean)
    vi_label = db.Column(db.Boolean)
    vi_exposed = db.Column(db.Boolean)

    # PASS / FAIL / N/A fields
    vi_repairs = db.Column(db.String(10))
    vi_strain = db.Column(db.String(10))
    vi_guards = db.Column(db.String(10))

    # Electrical tests
    earth_continuity_ohms = db.Column(db.String(50))
    insulation_mohms = db.Column(db.String(50))
    leakage_mA = db.Column(db.String(50))
    polarity_pass = db.Column(db.Boolean)

    # 5761 / 5762 fields
    condition_assessment = db.Column(db.String(255))
    functional_check = db.Column(db.String(255))
    accessories = db.Column(db.String(255))
    safe_for_resale = db.Column(db.String(255))

    repair_description = db.Column(db.Text)
    repaired_by = db.Column(db.String(255))
    parts_replaced = db.Column(db.Text)
    post_repair_test = db.Column(db.String(255))

    # Relationships
    appliance = db.relationship("Appliance", back_populates="tests")
    tester = db.relationship("Tester", back_populates="tests")
    photos = db.relationship("TestPhoto", back_populates="test", cascade="all, delete")


# ---------------------------------------------------------
# Test Photo Table
# ---------------------------------------------------------
class TestPhoto(db.Model):
    __tablename__ = "test_photo"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test_record.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)

    test = db.relationship("TestRecord", back_populates="photos")


# ---------------------------------------------------------
# Retest Rule Table
# ---------------------------------------------------------
class RetestRule(db.Model):
    __tablename__ = "retest_rule"

    id = db.Column(db.Integer, primary_key=True)
    class_type = db.Column(db.String(50))
    supply_type = db.Column(db.String(50))
    interval_days = db.Column(db.Integer, nullable=False)

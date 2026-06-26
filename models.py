from app import db

# Join table: test_record ↔ repair_record (many-to-many for AS/NZS 5762 verification)
test_repair_link = db.Table(
    'test_repair_link',
    db.Column('test_record_id',   db.Integer, db.ForeignKey('test_record.id'),   primary_key=True),
    db.Column('repair_record_id', db.Integer, db.ForeignKey('repair_record.id'), primary_key=True),
)

# ---------------------------------------------------------
# Tester Table
# ---------------------------------------------------------
class Tester(db.Model):
    __tablename__ = "tester"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    certificate_number = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(50))

    # Relationship to TestRecord (tester_id foreign key)
    tests = db.relationship("TestRecord", back_populates="tester", lazy=True)

    def __repr__(self):
        return f"<Tester {self.full_name} (Cert {self.certificate_number})>"


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
    serial_number = db.Column(db.String(255))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    disposed = db.Column(db.Boolean, default=False)
    disposal_date = db.Column(db.Date)
    disposal_price = db.Column(db.Numeric(10, 2))
    disposal_comment = db.Column(db.Text)

    new_to_service               = db.Column(db.Boolean, default=False)
    entry_to_service_date        = db.Column(db.Date)
    default_retest_interval_days = db.Column(db.Integer)

    @property
    def nts_next_test_due(self):
        if self.entry_to_service_date and self.default_retest_interval_days:
            from datetime import timedelta
            return self.entry_to_service_date + timedelta(days=self.default_retest_interval_days)
        return None

    tests = db.relationship("TestRecord", back_populates="appliance")
    repairs = db.relationship("RepairRecord", back_populates="appliance", cascade="all, delete")
    documents = db.relationship("ApplianceDocument", back_populates="appliance", cascade="all, delete")


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

    # Visual inspection — PASS/FAIL booleans
    vi_plug = db.Column(db.Boolean)
    vi_cord = db.Column(db.Boolean)
    vi_overheat = db.Column(db.Boolean)
    vi_exposed = db.Column(db.Boolean)

    # Visual inspection — explicit PASS / FAIL / N/A strings
    vi_casing = db.Column(db.String(50))
    vi_label = db.Column(db.String(50))
    vi_repairs = db.Column(db.String(10))
    vi_strain = db.Column(db.String(10))
    vi_guards = db.Column(db.String(10))

    # Electrical tests
    earth_continuity_ohms = db.Column(db.String(50))
    insulation_mohms = db.Column(db.String(50))
    leakage_mA = db.Column(db.String(50))
    polarity_pass = db.Column(db.String(50))

    # 5761 fields
    condition_assessment = db.Column(db.String(255))
    functional_check = db.Column(db.String(255))
    accessories = db.Column(db.String(255))
    safe_for_resale = db.Column(db.String(255))
    no_outstanding_recalls = db.Column(db.String(10))
    pins_insulated = db.Column(db.String(10))

    # 5762 — linked repair records (many-to-many)
    linked_repairs = db.relationship('RepairRecord', secondary='test_repair_link',
                                     backref=db.backref('verification_tests', lazy='dynamic'))

    # 5762 — structured functional tests (up to 5)
    func_test_1_method = db.Column(db.String(500))
    func_test_1_result = db.Column(db.String(10))
    func_test_2_method = db.Column(db.String(500))
    func_test_2_result = db.Column(db.String(10))
    func_test_3_method = db.Column(db.String(500))
    func_test_3_result = db.Column(db.String(10))
    func_test_4_method = db.Column(db.String(500))
    func_test_4_result = db.Column(db.String(10))
    func_test_5_method = db.Column(db.String(500))
    func_test_5_result = db.Column(db.String(10))

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
# Repair Record Table
# ---------------------------------------------------------
class RepairRecord(db.Model):
    __tablename__ = "repair_record"

    id = db.Column(db.Integer, primary_key=True)
    appliance_id = db.Column(db.Integer, db.ForeignKey("appliance.id"), nullable=False)
    repair_date = db.Column(db.Date, nullable=False)
    repaired_by = db.Column(db.String(255))
    description = db.Column(db.Text, nullable=False)
    comments = db.Column(db.Text)
    locked_by_test_date = db.Column(db.Date)
    disposed = db.Column(db.Boolean, default=False)
    parts_cost = db.Column(db.Numeric(10, 2))
    labour_minutes = db.Column(db.Integer)

    appliance = db.relationship("Appliance", back_populates="repairs")
    photos = db.relationship("RepairPhoto", back_populates="repair", cascade="all, delete")


# ---------------------------------------------------------
# Repair Photo Table
# ---------------------------------------------------------
class RepairPhoto(db.Model):
    __tablename__ = "repair_photo"

    id = db.Column(db.Integer, primary_key=True)
    repair_id = db.Column(db.Integer, db.ForeignKey("repair_record.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)

    repair = db.relationship("RepairRecord", back_populates="photos")


# ---------------------------------------------------------
# Appliance Document Table
# ---------------------------------------------------------
class ApplianceDocument(db.Model):
    __tablename__ = "appliance_document"

    id = db.Column(db.Integer, primary_key=True)
    appliance_id = db.Column(db.Integer, db.ForeignKey("appliance.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)

    appliance = db.relationship("Appliance", back_populates="documents")


# ---------------------------------------------------------
# Retest Rule Table
# ---------------------------------------------------------
class RetestRule(db.Model):
    __tablename__ = "retest_rule"

    id = db.Column(db.Integer, primary_key=True)
    class_type = db.Column(db.String(50))
    supply_type = db.Column(db.String(50))
    interval_days = db.Column(db.Integer, nullable=False)
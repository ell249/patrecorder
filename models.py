from app import db

# RCD Type -> Rating (mA), per AS/NZS 3760 (Type I = 10 mA, Type II = 30 mA)
RCD_RATING_MA_BY_TYPE = {"Type I": "10", "Type II": "30"}

# Fixed RCD retest intervals (days), per AS/NZS 3760:2022: push-button test every 6 months
# regardless of environment; trip-time test every 12 months (hostile/industrial) or 24
# months (non-hostile/office).
RCD_PUSH_BUTTON_INTERVAL_DAYS = 180
RCD_TRIP_TIME_INTERVAL_DAYS_BY_ENVIRONMENT = {"HOSTILE": 365, "NON_HOSTILE": 730}

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

    switchboard_id = db.Column(db.Integer, db.ForeignKey("switchboard.id"))

    # Fixed RCD hardware properties (set once when the RCD is registered, not per-test)
    rcd_type = db.Column(db.String(20))       # "Type I" | "Type II"
    rcd_waveform = db.Column(db.String(10))   # "AC" | "A" | "B" | "F" — informational only

    @property
    def nts_next_test_due(self):
        if self.entry_to_service_date and self.default_retest_interval_days:
            from datetime import timedelta
            return self.entry_to_service_date + timedelta(days=self.default_retest_interval_days)
        return None

    @property
    def rcd_rating_ma(self):
        return RCD_RATING_MA_BY_TYPE.get(self.rcd_type)

    tests = db.relationship("TestRecord", back_populates="appliance")
    repairs = db.relationship("RepairRecord", back_populates="appliance", cascade="all, delete")
    documents = db.relationship("ApplianceDocument", back_populates="appliance", cascade="all, delete")
    switchboard = db.relationship("Switchboard", back_populates="rcds")


# ---------------------------------------------------------
# Switchboard Table
# ---------------------------------------------------------
class Switchboard(db.Model):
    __tablename__ = "switchboard"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    notes = db.Column(db.Text)
    environment = db.Column(db.String(20))  # "HOSTILE" | "NON_HOSTILE"
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    rcds = db.relationship("Appliance", back_populates="switchboard")

    @property
    def push_button_interval_days(self):
        return RCD_PUSH_BUTTON_INTERVAL_DAYS

    @property
    def trip_time_interval_days(self):
        # Default to the more conservative (hostile) interval when not yet classified.
        return RCD_TRIP_TIME_INTERVAL_DAYS_BY_ENVIRONMENT.get(self.environment, RCD_TRIP_TIME_INTERVAL_DAYS_BY_ENVIRONMENT["HOSTILE"])


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

    # RCD (Lead+RCD / Fixed RCD)
    rcd_type = db.Column(db.String(20))                    # "Type I" | "Type II"
    rcd_waveform = db.Column(db.String(10))                 # "AC" | "A" | "B" | "F" — informational only
    rcd_test_method = db.Column(db.String(20))              # "Push Button" | "Trip Time"
    rcd_push_button_result = db.Column(db.String(10))       # "PASS" | "FAIL"
    rcd_trip_time_0deg_ms = db.Column(db.String(20))
    rcd_trip_time_0deg_result = db.Column(db.String(10))    # server-computed
    rcd_trip_time_180deg_ms = db.Column(db.String(20))
    rcd_trip_time_180deg_result = db.Column(db.String(10))  # server-computed

    @property
    def rcd_rating_ma(self):
        return RCD_RATING_MA_BY_TYPE.get(self.rcd_type)

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
USE test_and_tag;

-- Drop in reverse dependency order (safe to re-run on a fresh database)
-- DROP TABLE IF EXISTS repair_photo;
-- DROP TABLE IF EXISTS repair_record;
-- DROP TABLE IF EXISTS test_photo;
-- DROP TABLE IF EXISTS test_record;
-- DROP TABLE IF EXISTS appliance;
-- DROP TABLE IF EXISTS retest_rule;
-- DROP TABLE IF EXISTS tester;

-- ---------------------------------------------------------
-- TESTER
-- ---------------------------------------------------------
CREATE TABLE tester (
    id                 INT          AUTO_INCREMENT PRIMARY KEY,
    full_name          VARCHAR(120) NOT NULL,
    certificate_number VARCHAR(120) NOT NULL,
    phone_number       VARCHAR(50)
);

-- ---------------------------------------------------------
-- APPLIANCE
-- ---------------------------------------------------------
CREATE TABLE appliance (
    id               INT            AUTO_INCREMENT PRIMARY KEY,
    asset_number     VARCHAR(255)   NOT NULL UNIQUE,
    description      VARCHAR(255),
    make_model       VARCHAR(255),
    location         VARCHAR(255),
    owner            VARCHAR(255),
    class_type       VARCHAR(50),
    supply_type      VARCHAR(50),
    serial_number    VARCHAR(255),
    purchase_date    DATE,
    purchase_price   DECIMAL(10,2),
    receipt_filepath VARCHAR(255),
    created_at       DATETIME       DEFAULT CURRENT_TIMESTAMP,
    disposed         BOOLEAN        DEFAULT FALSE,
    disposal_date    DATE,
    disposal_price   DECIMAL(10,2),
    disposal_comment TEXT
);

-- ---------------------------------------------------------
-- TEST RECORD
-- ---------------------------------------------------------
CREATE TABLE test_record (
    id             INT          AUTO_INCREMENT PRIMARY KEY,

    appliance_id   INT          NOT NULL,
    tester_id      INT          NOT NULL,

    test_date      DATE         NOT NULL,
    test_type      VARCHAR(255) NOT NULL,
    test_standard  VARCHAR(50)  NOT NULL,
    tag_number     VARCHAR(255) NOT NULL,

    next_test_due  DATE,
    overall_result VARCHAR(10)  NOT NULL,
    comments       TEXT,
    disposed       BOOLEAN      DEFAULT FALSE,

    -- Visual inspection — PASS / FAIL (boolean stored as TINYINT)
    vi_plug        BOOLEAN,
    vi_cord        BOOLEAN,
    vi_overheat    BOOLEAN,
    vi_exposed     BOOLEAN,

    -- Visual inspection — explicit PASS / FAIL / N/A string
    vi_casing      VARCHAR(50),
    vi_label       VARCHAR(50),
    vi_repairs     VARCHAR(10),
    vi_strain      VARCHAR(10),
    vi_guards      VARCHAR(10),

    -- Electrical tests
    earth_continuity_ohms VARCHAR(50),
    insulation_mohms      VARCHAR(50),
    leakage_mA            VARCHAR(50),
    polarity_pass         VARCHAR(50),

    -- AS/NZS 5761 fields
    condition_assessment  VARCHAR(255),
    functional_check      VARCHAR(255),
    accessories           VARCHAR(255),
    safe_for_resale       VARCHAR(255),

    -- AS/NZS 5762 fields
    repair_description    TEXT,
    repaired_by           VARCHAR(255),
    parts_replaced        TEXT,
    post_repair_test      VARCHAR(255),

    FOREIGN KEY (appliance_id) REFERENCES appliance(id) ON DELETE CASCADE,
    FOREIGN KEY (tester_id)    REFERENCES tester(id)
);

-- ---------------------------------------------------------
-- TEST PHOTO
-- ---------------------------------------------------------
CREATE TABLE test_photo (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    test_id  INT          NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    FOREIGN KEY (test_id) REFERENCES test_record(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- REPAIR RECORD
-- ---------------------------------------------------------
CREATE TABLE repair_record (
    id                  INT           AUTO_INCREMENT PRIMARY KEY,
    appliance_id        INT           NOT NULL,
    repair_date         DATE          NOT NULL,
    repaired_by         VARCHAR(255),
    description         TEXT          NOT NULL,
    comments            TEXT,
    locked_by_test_date DATE,
    disposed            BOOLEAN       DEFAULT FALSE,
    parts_cost          DECIMAL(10,2),
    labour_minutes      INT,
    FOREIGN KEY (appliance_id) REFERENCES appliance(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- REPAIR PHOTO
-- ---------------------------------------------------------
CREATE TABLE repair_photo (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    repair_id INT          NOT NULL,
    filename  VARCHAR(255) NOT NULL,
    filepath  VARCHAR(255) NOT NULL,
    FOREIGN KEY (repair_id) REFERENCES repair_record(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- RETEST RULE
-- ---------------------------------------------------------
CREATE TABLE retest_rule (
    id            INT         AUTO_INCREMENT PRIMARY KEY,
    class_type    VARCHAR(50),
    supply_type   VARCHAR(50),
    interval_days INT         NOT NULL
);

-- DROP TABLE IF EXISTS test_photo;
-- DROP TABLE IF EXISTS test_record;
-- DROP TABLE IF EXISTS appliance;
-- DROP TABLE IF EXISTS retest_rule;
-- DROP TABLE IF EXISTS tester;

-- ---------------------------------------------------------
-- TESTER TABLE
-- ---------------------------------------------------------
CREATE TABLE tester (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    certificate_number VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50)
);

-- ---------------------------------------------------------
-- APPLIANCE TABLE
-- ---------------------------------------------------------
CREATE TABLE appliance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_number VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    make_model VARCHAR(255),
    location VARCHAR(255),
    owner VARCHAR(255),
    class_type VARCHAR(50),
    supply_type VARCHAR(50),
    disposed BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------
-- TEST RECORD TABLE
-- ---------------------------------------------------------
CREATE TABLE test_record (
    id INT AUTO_INCREMENT PRIMARY KEY,

    appliance_id INT NOT NULL,
    tester_id INT NOT NULL,

    test_date DATE NOT NULL,
    test_type VARCHAR(255) NOT NULL,
    test_standard VARCHAR(50) NOT NULL,
    tag_number VARCHAR(255) NOT NULL,

    next_test_due DATE,
    overall_result VARCHAR(10) NOT NULL,
    comments TEXT,
    disposed BOOLEAN DEFAULT FALSE,

    -- Visual inspection (boolean PASS/FAIL)
    vi_plug BOOLEAN,
    vi_cord BOOLEAN,
    vi_casing BOOLEAN,
    vi_overheat BOOLEAN,
    vi_label BOOLEAN,
    vi_exposed BOOLEAN,

    -- PASS / FAIL / N/A fields
    vi_repairs VARCHAR(10),
    vi_strain VARCHAR(10),
    vi_guards VARCHAR(10),

    -- Electrical tests
    earth_continuity_ohms VARCHAR(50),
    insulation_mohms VARCHAR(50),
    leakage_mA VARCHAR(50),
    polarity_pass BOOLEAN,

    -- 5761 fields
    condition_assessment VARCHAR(255),
    functional_check VARCHAR(255),
    accessories VARCHAR(255),
    safe_for_resale VARCHAR(255),

    -- 5762 fields
    repair_description TEXT,
    repaired_by VARCHAR(255),
    parts_replaced TEXT,
    post_repair_test VARCHAR(255),

    FOREIGN KEY (appliance_id) REFERENCES appliance(id) ON DELETE CASCADE,
    FOREIGN KEY (tester_id) REFERENCES tester(id)
);

-- ---------------------------------------------------------
-- TEST PHOTO TABLE
-- ---------------------------------------------------------
CREATE TABLE test_photo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    FOREIGN KEY (test_id) REFERENCES test_record(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- RETEST RULE TABLE
-- ---------------------------------------------------------
CREATE TABLE retest_rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_type VARCHAR(50),
    supply_type VARCHAR(50),
    interval_days INT NOT NULL
);

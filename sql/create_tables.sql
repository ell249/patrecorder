-- -----------------------------------------------------
-- Database: test_and_tag   (or your chosen DB name)
-- -----------------------------------------------------

CREATE TABLE appliance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_number VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(255),
    make_model VARCHAR(255),
    location VARCHAR(255),
    owner VARCHAR(255),
    class_type VARCHAR(50),
    supply_type VARCHAR(50),
    disposed TINYINT(1) DEFAULT 0
);

-- -----------------------------------------------------
-- Test Records
-- -----------------------------------------------------

CREATE TABLE test_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appliance_id INT NOT NULL,

    test_date DATE NOT NULL,
    tester_name VARCHAR(255) NOT NULL,
    test_type VARCHAR(255) NOT NULL,
    test_standard VARCHAR(50) NOT NULL,
    tag_number VARCHAR(255) NOT NULL,

    -- Visual Inspection (boolean PASS/FAIL)
    vi_plug TINYINT(1) DEFAULT 0,
    vi_cord TINYINT(1) DEFAULT 0,
    vi_casing TINYINT(1) DEFAULT 0,
    vi_overheat TINYINT(1) DEFAULT 0,
    vi_label TINYINT(1) DEFAULT 0,
    vi_exposed TINYINT(1) DEFAULT 0,

    -- Visual Inspection (PASS / FAIL / N/A)
    vi_repairs VARCHAR(10),
    vi_strain VARCHAR(10),
    vi_guards VARCHAR(10),

    -- Electrical Tests
    visual_pass TINYINT(1) DEFAULT 0,
    earth_continuity_ohms VARCHAR(50),
    insulation_mohms VARCHAR(50),
    polarity_pass TINYINT(1) DEFAULT 0,
    leakage_mA VARCHAR(50),

    overall_result VARCHAR(10) NOT NULL,
    next_test_due DATE,
    comments TEXT,

    -- 5761 / 5762 fields
    condition_assessment VARCHAR(255),
    functional_check VARCHAR(255),
    accessories VARCHAR(255),
    safe_for_resale VARCHAR(255),

    repair_description TEXT,
    repaired_by VARCHAR(255),
    parts_replaced TEXT,
    post_repair_test VARCHAR(255),

    disposed TINYINT(1) DEFAULT 0,

    CONSTRAINT fk_test_appliance
        FOREIGN KEY (appliance_id)
        REFERENCES appliance(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Test Photos
-- -----------------------------------------------------

CREATE TABLE test_photo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,

    CONSTRAINT fk_photo_test
        FOREIGN KEY (test_id)
        REFERENCES test_record(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Retest Rules
-- -----------------------------------------------------

CREATE TABLE retest_rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_type VARCHAR(50),
    supply_type VARCHAR(50),
    interval_days INT NOT NULL
);

CREATE DATABASE IF NOT EXISTS test_and_tag;
USE test_and_tag;

DROP TABLE IF EXISTS appliance;

CREATE TABLE appliance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_number VARCHAR(64) NOT NULL UNIQUE,
    description VARCHAR(255),
    make_model VARCHAR(255),                    -- NEW FIELD
    location VARCHAR(255),
    owner VARCHAR(255),
    class_type VARCHAR(64),
    supply_type VARCHAR(64),
    disposed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS test_record;

CREATE TABLE test_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appliance_id INT NOT NULL,

    test_date DATETIME,
    tester_name VARCHAR(255),
    test_type VARCHAR(255),
    test_standard VARCHAR(32),
    tag_number VARCHAR(64),

    visual_pass BOOLEAN,
    earth_continuity_ohms VARCHAR(64),
    insulation_mohms VARCHAR(64),
    polarity_pass BOOLEAN,
    leakage_mA VARCHAR(64),

    overall_result VARCHAR(16),
    next_test_due DATE,
    comments TEXT,

    condition_assessment VARCHAR(255),
    functional_check VARCHAR(255),
    accessories VARCHAR(255),
    safe_for_resale VARCHAR(255),

    repair_description TEXT,
    repaired_by VARCHAR(255),
    parts_replaced VARCHAR(255),
    post_repair_test VARCHAR(255),

    disposed BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (appliance_id) REFERENCES appliance(id)
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS test_photo;

CREATE TABLE test_photo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    filename VARCHAR(255),
    filepath VARCHAR(255),

    FOREIGN KEY (test_id) REFERENCES test_record(id)
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS retest_rule;

CREATE TABLE retest_rule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_type VARCHAR(64) NOT NULL,
    supply_type VARCHAR(64) NOT NULL,
    interval_days INT NOT NULL,
    description VARCHAR(255),
    priority INT DEFAULT 0
);

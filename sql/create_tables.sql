USE test_and_tag;

CREATE TABLE appliances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asset_number VARCHAR(64) NOT NULL UNIQUE,
    description VARCHAR(255),
    location VARCHAR(255),
    owner VARCHAR(255),
    class_type VARCHAR(32),
    supply_type VARCHAR(32),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appliance_id INT NOT NULL,
    test_date DATETIME NOT NULL,
    tester_name VARCHAR(255),
    test_type VARCHAR(64),
    test_standard VARCHAR(16) DEFAULT '3760',
    tag_number VARCHAR(64),
    visual_pass TINYINT(1) DEFAULT 0,
    earth_continuity_ohms DECIMAL(10,3),
    insulation_mohms DECIMAL(10,3),
    polarity_pass TINYINT(1),
    leakage_mA DECIMAL(10,3),
    overall_result VARCHAR(16),
    next_test_due DATE,
    comments TEXT,
    condition_assessment TEXT,
    functional_check TEXT,
    accessories VARCHAR(255),
    safe_for_resale VARCHAR(8),
    repair_description TEXT,
    repaired_by VARCHAR(255),
    parts_replaced TEXT,
    post_repair_test TEXT,
    CONSTRAINT fk_tests_appliance
      FOREIGN KEY (appliance_id) REFERENCES appliances(id)
      ON DELETE CASCADE
);

CREATE TABLE test_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_photos_test
      FOREIGN KEY (test_id) REFERENCES tests(id)
      ON DELETE CASCADE
);

CREATE TABLE retest_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_type VARCHAR(32),      -- 'CLASS I', 'CLASS II', 'ANY'
    supply_type VARCHAR(64),     -- 'PORTABLE', 'FIXED', 'CONSTRUCTION', 'ANY'
    interval_days INT NOT NULL,
    description VARCHAR(255),
    priority INT DEFAULT 0
);

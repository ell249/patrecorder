USE test_and_tag;

INSERT INTO retest_rules (class_type, supply_type, interval_days, description, priority) VALUES
('CLASS I', 'PORTABLE', 180, '6 months — Portable Class I equipment, moderate-risk areas', 20),
('CLASS I', 'ANY',      365, '12 months — Class I equipment in low-risk areas', 10),
('CLASS II', 'PORTABLE',365, '12 months — Portable Class II equipment', 15),
('CLASS II', 'ANY',     730, '24 months — Fixed Class II equipment in controlled environments', 10),
('ANY', 'CONSTRUCTION', 90,  '3 months — High-risk environments (construction, workshops, factories)', 30),
('ANY', 'ANY',          365, '12 months — Default interval', 1);

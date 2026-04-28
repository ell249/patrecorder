USE test_and_tag;

-- Default retest interval rules per AS/NZS 3760:2022 guidance.
-- The application selects the most specific matching rule (class_type + supply_type).
-- The 'ANY' wildcard rows act as fallbacks.

INSERT INTO retest_rule (class_type, supply_type, interval_days) VALUES
('ANY',      'ANY',          365),   -- Default: 12 months
('CLASS I',  'ANY',          365),   -- Class I, general: 12 months
('CLASS I',  'PORTABLE',     180),   -- Class I, portable: 6 months
('CLASS II', 'ANY',          730),   -- Class II, general: 24 months
('CLASS II', 'PORTABLE',     365),   -- Class II, portable: 12 months
('ANY',      'CONSTRUCTION',  90);   -- High-risk environments: 3 months

ALTER TABLE plantations ADD COLUMN site_class text DEFAULT 'archived'
CHECK (site_class IN ('real_verified', 'synthetic_demo', 'archived'));

UPDATE plantations SET site_class = 'real_verified' WHERE id = 'f1000001-0000-0000-0000-000000000001';
UPDATE plantations SET site_class = 'real_verified' WHERE id = 'f2000002-0000-0000-0000-000000000002';
UPDATE plantations SET site_class = 'synthetic_demo' WHERE id = 'a1000001-0000-0000-0000-000000000001';
UPDATE plantations SET site_class = 'synthetic_demo' WHERE id = 'a1000001-0000-0000-0000-000000000002';
UPDATE plantations SET site_class = 'archived' WHERE id = 'a1000001-0000-0000-0000-000000000003';
UPDATE plantations SET site_class = 'archived' WHERE id = 'a1000001-0000-0000-0000-000000000004';
UPDATE plantations SET site_class = 'archived' WHERE id = 'a1000001-0000-0000-0000-000000000005';

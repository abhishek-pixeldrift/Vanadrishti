-- Make planting_date nullable in plantations
ALTER TABLE plantations
ALTER COLUMN planting_date DROP NOT NULL;

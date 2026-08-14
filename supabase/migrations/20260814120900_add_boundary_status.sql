-- Migration to add boundary_status to plantation_boundaries
ALTER TABLE plantation_boundaries
ADD COLUMN boundary_status TEXT DEFAULT 'unknown';

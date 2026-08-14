-- Migration to add pending_location_review and flagged_location to verification_status constraint
ALTER TABLE field_visits DROP CONSTRAINT IF EXISTS field_visits_verification_status_check;

ALTER TABLE field_visits ADD CONSTRAINT field_visits_verification_status_check 
CHECK (verification_status IN ('pending', 'verified', 'flagged', 'rejected', 'pending_location_review', 'flagged_location'));

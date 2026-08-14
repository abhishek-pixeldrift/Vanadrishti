-- Migration to update alerts.alert_type check constraint for Phase 9
-- Add 'dynamic_risk_critical' to the list of allowed values

ALTER TABLE alerts
DROP CONSTRAINT IF EXISTS alerts_alert_type_check;

ALTER TABLE alerts
ADD CONSTRAINT alerts_alert_type_check 
CHECK (alert_type IN (
    'ndvi_decline', 
    'maintenance_overdue', 
    'verification_failed', 
    'high_risk', 
    'low_survival', 
    'dynamic_risk_critical'
));

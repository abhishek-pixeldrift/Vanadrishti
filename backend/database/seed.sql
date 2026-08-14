-- ============================================
-- EcoTrack Seed Data
-- 5 Demo Plantations in Maharashtra
-- Each tells a different monitoring story
-- ============================================
-- NOTE: This is PROTOTYPE seed data for demo purposes.
-- It does not represent real plantation records.
-- ============================================

-- ============================================
-- PLANTATIONS
-- ============================================
INSERT INTO plantations (id, name, district, state, area_hectares, saplings_planted, current_saplings, planting_date, status, risk_score, latitude, longitude) VALUES

-- 1. Healthy plantation — steady growth success story
('a1000001-0000-0000-0000-000000000001',
 'Nashik Hills Block A', 'Nashik', 'Maharashtra',
 12.5, 5000, 4750, '2025-06-15', 'healthy', 22,
 20.0063, 73.7910),

-- 2. Warning — recent NDVI decline, needs attention
('a1000001-0000-0000-0000-000000000002',
 'Pune Western Ghats B', 'Pune', 'Maharashtra',
 8.3, 3200, 2800, '2025-04-10', 'warning', 58,
 18.5204, 73.8567),

-- 3. Critical — sharp decline, no maintenance in 90 days
('a1000001-0000-0000-0000-000000000003',
 'Ratnagiri Coastal C', 'Ratnagiri', 'Maharashtra',
 15.0, 6000, 2400, '2025-03-01', 'critical', 87,
 16.9944, 73.3000),

-- 4. Healthy — recovered after maintenance intervention
('a1000001-0000-0000-0000-000000000004',
 'Satara Ridge D', 'Satara', 'Maharashtra',
 10.0, 4000, 3600, '2025-05-20', 'healthy', 30,
 17.6805, 74.0183),

-- 5. Warning — stagnant/flat growth, ambiguous
('a1000001-0000-0000-0000-000000000005',
 'Aurangabad Plateau E', 'Chhatrapati Sambhajinagar', 'Maharashtra',
 6.7, 2500, 2100, '2025-07-01', 'warning', 52,
 19.8762, 75.3433);


-- ============================================
-- NDVI OBSERVATIONS (monthly, 12 months each)
-- ============================================

-- Plantation 1: Nashik — Steady upward trend (success)
INSERT INTO ndvi_observations (plantation_id, observation_date, ndvi_value, health_status, data_source) VALUES
('a1000001-0000-0000-0000-000000000001', '2025-07-15', 0.22, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2025-08-15', 0.28, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2025-09-15', 0.35, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2025-10-15', 0.41, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2025-11-15', 0.45, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2025-12-15', 0.43, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-01-15', 0.40, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-02-15', 0.38, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-03-15', 0.42, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-04-15', 0.48, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-05-15', 0.52, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000001', '2026-06-15', 0.55, 'excellent', 'seed');

-- Plantation 2: Pune — Recent decline (warning story)
INSERT INTO ndvi_observations (plantation_id, observation_date, ndvi_value, health_status, data_source) VALUES
('a1000001-0000-0000-0000-000000000002', '2025-05-10', 0.20, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-06-10', 0.30, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-07-10', 0.38, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-08-10', 0.44, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-09-10', 0.48, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-10-10', 0.50, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-11-10', 0.47, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2025-12-10', 0.42, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2026-01-10', 0.38, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2026-02-10', 0.33, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2026-03-10', 0.28, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000002', '2026-04-10', 0.25, 'moderate', 'seed');

-- Plantation 3: Ratnagiri — Sharp decline (critical story)
INSERT INTO ndvi_observations (plantation_id, observation_date, ndvi_value, health_status, data_source) VALUES
('a1000001-0000-0000-0000-000000000003', '2025-04-01', 0.18, 'poor', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-05-01', 0.25, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-06-01', 0.35, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-07-01', 0.42, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-08-01', 0.45, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-09-01', 0.40, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-10-01', 0.32, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-11-01', 0.25, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2025-12-01', 0.18, 'poor', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2026-01-01', 0.14, 'poor', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2026-02-01', 0.11, 'poor', 'seed'),
('a1000001-0000-0000-0000-000000000003', '2026-03-01', 0.09, 'poor', 'seed');

-- Plantation 4: Satara — Recovery after maintenance (success story)
INSERT INTO ndvi_observations (plantation_id, observation_date, ndvi_value, health_status, data_source) VALUES
('a1000001-0000-0000-0000-000000000004', '2025-06-20', 0.25, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-07-20', 0.33, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-08-20', 0.38, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-09-20', 0.35, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-10-20', 0.28, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-11-20', 0.22, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2025-12-20', 0.20, 'poor', 'seed'),
-- ^ Maintenance intervention happened here
('a1000001-0000-0000-0000-000000000004', '2026-01-20', 0.24, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2026-02-20', 0.30, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2026-03-20', 0.38, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2026-04-20', 0.45, 'good', 'seed'),
('a1000001-0000-0000-0000-000000000004', '2026-05-20', 0.50, 'good', 'seed');

-- Plantation 5: Aurangabad — Stagnant/flat growth (ambiguous)
INSERT INTO ndvi_observations (plantation_id, observation_date, ndvi_value, health_status, data_source) VALUES
('a1000001-0000-0000-0000-000000000005', '2025-08-01', 0.20, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2025-09-01', 0.24, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2025-10-01', 0.26, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2025-11-01', 0.27, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2025-12-01', 0.25, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-01-01', 0.24, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-02-01', 0.26, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-03-01', 0.27, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-04-01', 0.25, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-05-01', 0.28, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-06-01', 0.26, 'moderate', 'seed'),
('a1000001-0000-0000-0000-000000000005', '2026-07-01', 0.27, 'moderate', 'seed');


-- ============================================
-- FIELD VISITS (sample visits)
-- ============================================
INSERT INTO field_visits (plantation_id, worker_name, gps_lat, gps_lng, gps_accuracy, visit_timestamp, notes, verification_status) VALUES

-- Nashik — routine healthy visit
('a1000001-0000-0000-0000-000000000001', 'Ramesh Patil', 20.0065, 73.7912, 4.5,
 '2026-05-20 09:30:00+05:30', 'Saplings growing well. Good canopy cover developing.', 'verified'),

-- Pune — recent visit noting decline
('a1000001-0000-0000-0000-000000000002', 'Suresh Deshmukh', 18.5206, 73.8570, 6.2,
 '2026-03-15 10:00:00+05:30', 'Several saplings showing stress. Dry soil conditions observed.', 'verified'),

-- Ratnagiri — last visit was 90+ days ago
('a1000001-0000-0000-0000-000000000003', 'Vikram Jadhav', 16.9946, 73.3002, 8.1,
 '2026-01-10 11:00:00+05:30', 'Many saplings dead or dying. Cattle grazing damage visible.', 'flagged'),

-- Satara — post-maintenance recovery visit
('a1000001-0000-0000-0000-000000000004', 'Anand Kulkarni', 17.6807, 74.0185, 3.8,
 '2026-04-25 08:45:00+05:30', 'Recovery visible after watering campaign. New growth emerging.', 'verified'),
('a1000001-0000-0000-0000-000000000004', 'Anand Kulkarni', 17.6806, 74.0184, 4.0,
 '2026-01-05 09:00:00+05:30', 'Saplings stressed. Recommended immediate watering.', 'verified'),

-- Aurangabad — recent visit
('a1000001-0000-0000-0000-000000000005', 'Priya Shinde', 19.8764, 75.3435, 5.5,
 '2026-06-10 10:30:00+05:30', 'Growth seems stagnant. Soil quality may be a factor.', 'verified');


-- ============================================
-- ALERTS
-- ============================================
INSERT INTO alerts (plantation_id, alert_type, severity, message, acknowledged) VALUES

-- Ratnagiri critical alerts
('a1000001-0000-0000-0000-000000000003', 'ndvi_decline', 'critical',
 'NDVI dropped from 0.45 to 0.09 over 7 months. Severe vegetation loss detected.', false),
('a1000001-0000-0000-0000-000000000003', 'maintenance_overdue', 'critical',
 'No field visit recorded in 90+ days. Immediate inspection required.', false),
('a1000001-0000-0000-0000-000000000003', 'low_survival', 'high',
 'Current sapling count (2400) is 60% below planted count (6000).', false),

-- Pune warning alerts
('a1000001-0000-0000-0000-000000000002', 'ndvi_decline', 'medium',
 'NDVI declining for 6 consecutive months. From 0.50 to 0.25.', false),

-- Aurangabad stagnation alert
('a1000001-0000-0000-0000-000000000005', 'ndvi_decline', 'low',
 'NDVI has remained flat (0.24-0.28) for 12 months. Growth stagnation detected.', false);


-- ============================================
-- MAINTENANCE TASKS
-- ============================================
INSERT INTO maintenance_tasks (plantation_id, problem, risk_level, recommended_action, assigned_to, due_date, status) VALUES

-- Ratnagiri — urgent tasks
('a1000001-0000-0000-0000-000000000003',
 'Severe vegetation decline — potential total plantation failure',
 'high', 'Emergency field inspection + sapling replacement + fencing against cattle',
 'Vikram Jadhav', '2026-08-15', 'pending'),

('a1000001-0000-0000-0000-000000000003',
 'No maintenance activity in 90+ days',
 'high', 'Immediate watering and weeding required',
 'Vikram Jadhav', '2026-08-12', 'assigned'),

-- Pune — moderate task
('a1000001-0000-0000-0000-000000000002',
 'Declining vegetation health over 6 months',
 'medium', 'Soil assessment and targeted watering campaign',
 'Suresh Deshmukh', '2026-08-20', 'pending'),

-- Satara — completed task (success story)
('a1000001-0000-0000-0000-000000000004',
 'Vegetation stress detected in Dec 2025',
 'medium', 'Emergency watering + soil treatment',
 'Anand Kulkarni', '2026-01-15', 'completed');

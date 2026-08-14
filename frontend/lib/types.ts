export interface Plantation {
  id: string;
  name: string;
  district: string;
  state: string;
  area_hectares: number;
  planting_date: string;
  status: 'healthy' | 'warning' | 'critical';
  site_class?: 'real_verified' | 'synthetic_demo' | 'archived' | string;
  risk_score: number;
  latitude: number;
  longitude: number;
  boundary_status?: string;
  boundary_geojson?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  plantation_id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_plantations: number;
  healthy_count: number;
  at_risk_count: number;
  active_alerts: number;
}

export interface NDVIObservation {
  id: string;
  plantation_id: string;
  observation_date: string;
  ndvi_value: number | null;
  health_status: 'poor' | 'moderate' | 'good' | 'excellent' | 'missing' | string;
  data_source: string;
  created_at: string;
}

export interface FieldVisit {
  id: string;
  plantation_id: string;
  worker_name: string;
  gps_lat?: number;
  gps_lng?: number;
  gps_accuracy?: number;
  gps_altitude?: number;
  gps_heading?: number;
  gps_speed?: number;
  client_timestamp?: string;
  server_timestamp?: string;
  user_agent?: string;
  location_confidence?: Record<string, unknown>;
  photo_url?: string;
  notes?: string;
  verification_status: 'pending' | 'verified' | 'flagged' | 'rejected';
  visit_timestamp: string;
  created_at: string;
}

export interface AIVerification {
  id?: string;
  field_visit_id?: string;
  tree_detected: boolean;
  health_assessment: 'poor' | 'moderate' | 'good' | 'excellent';
  condition_notes: string;
  confidence: number;
  created_at?: string;
  
  // Phase 7 Gating
  status?: string;
  message?: string;
  location_confidence?: Record<string, unknown>;
}

export interface RiskComponent {
  score: number;
  max: number;
  source: string;
  [key: string]: unknown;
}

export interface RiskResult {
  plantation_id: string;
  risk_score: number;
  risk_level: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  components: {
    ndvi: RiskComponent;
    ai_health: RiskComponent;
    visit_recency: RiskComponent;
    maintenance: RiskComponent;
    location_trust: RiskComponent;
  };
  missing_inputs: string[];
  generated_at: string;
}


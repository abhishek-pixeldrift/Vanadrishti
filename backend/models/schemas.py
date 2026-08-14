from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# Plantation Schemas
class PlantationBase(BaseModel):
    name: str
    district: str
    state: str = "Maharashtra"
    area_hectares: float
    saplings_planted: int
    current_saplings: Optional[int] = None
    planting_date: Optional[date] = None
    status: str = "healthy"
    site_class: str = "real_verified"
    risk_score: int = 50
    latitude: float
    longitude: float

class Plantation(PlantationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Alert(BaseModel):
    id: UUID
    plantation_id: UUID
    alert_type: str
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardStats(BaseModel):
    total_plantations: int
    healthy_count: int
    at_risk_count: int
    active_alerts: int

class NDVIObservation(BaseModel):
    id: UUID
    plantation_id: UUID
    observation_date: date
    ndvi_value: Optional[float] = None
    health_status: str
    data_source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FieldVisitCreate(BaseModel):
    plantation_id: UUID
    worker_name: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy: Optional[float] = None
    gps_altitude: Optional[float] = None
    gps_heading: Optional[float] = None
    gps_speed: Optional[float] = None
    client_timestamp: Optional[datetime] = None
    user_agent: Optional[str] = None
    location_confidence: Optional[dict] = None
    notes: Optional[str] = None

class FieldVisit(FieldVisitCreate):
    id: UUID
    photo_url: Optional[str] = None
    server_timestamp: Optional[datetime] = None
    visit_timestamp: datetime
    verification_status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AIVerification(BaseModel):
    id: Optional[UUID] = None
    field_visit_id: Optional[UUID] = None
    tree_detected: bool
    health_assessment: str
    condition_notes: str
    confidence: float
    created_at: Optional[datetime] = None
    
    # Phase 7 Gating fields
    status: Optional[str] = "verified"
    message: Optional[str] = None
    location_confidence: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)

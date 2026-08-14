"""
EcoTrack Backend — FastAPI Application
Satellite-Verified Lifecycle Monitoring for Compensatory Afforestation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from routers import plantations, ndvi, field_visits, alerts, boundaries, maintenance, notifications

load_dotenv()

app = FastAPI(
    title="EcoTrack API",
    description="Geo-tagged Monitoring System for Compensatory Afforestation",
    version="0.1.0",
)

# Mount static files for image uploads
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plantations.router)
app.include_router(ndvi.router)
app.include_router(field_visits.router)
app.include_router(alerts.router)
app.include_router(boundaries.router)
app.include_router(maintenance.router)
app.include_router(notifications.router)

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "project": "EcoTrack", "version": "0.1.0"}


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "pending_setup",
            "ai": "pending_setup",
        },
    }

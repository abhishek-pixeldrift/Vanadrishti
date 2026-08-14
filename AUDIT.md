# EcoTrack Project Audit

## 1. Project Structure
The project is divided into `frontend/` and `backend/`.

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** CSS Modules, `globals.css`
- **Key Dependencies:** React, Mapbox GL JS, Recharts, Framer Motion, Lucide React
- **Architecture:** 
  - `app/page.tsx`: Dashboard with Mapbox map, stats, alerts, and risk engine runner.
  - `app/field/page.tsx`: Field visit data capture with camera (EXIF) and GPS (GPSLocator), plus AI Verification.
  - `app/plantations/[id]/page.tsx`: Plantation details, NDVI charts.
  - `app/login/page.tsx`: Role-based login (citizen vs officer).
  - `lib/api.ts`: API service layer to communicate with the FastAPI backend.
  - `components/map/`: Contains `PlantationMap.tsx` running on Mapbox GL JS.

### Backend
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL with PostGIS extension enabled)
- **Core Files:**
  - `main.py`: FastAPI entry point.
  - `database/schema.sql`: Core schema (plantations, field_visits, ai_verifications, alerts, ndvi_observations) with PostGIS geometries.
  - `routers/`: API route handlers for field visits, plantations, NDVI, alerts.
  - `services/ai_service.py`: Gemini-based AI verification logic.

## 2. Status & Integrations
- **Map Implementation:** Currently using Mapbox GL JS with satellite tiles, diamond markers, and styled popups.
- **Satellite Integration:** Failsafe mock data exists for NDVI fetching on map click; intended for Sentinel-2 via Planetary Computer / Sentinel Hub.
- **AI Verification:** Gemini AI is integrated for analyzing field visit photos for tree detection and health assessment.
- **Database Consistency:** Live database contains Nashik, Thane, and Kopargaon correctly configured for presentation.

## 3. Next Steps (Phase 2+)
- Fully connect live Sentinel-2 API for NDVI processing.
- Complete the role-based dashboards and alert mechanics.

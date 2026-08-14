# Vanadrishti

**Forest Sight / Geo-Intelligence for Plantation Monitoring**

## 1. Project Overview
Monitoring compensatory afforestation is challenging due to the absence of reliable tracking mechanisms, resulting in poor sapling survival and limited accountability. Vanadrishti is a geo-tagged monitoring system designed to track plantation activities and maintenance throughout the plantation lifecycle.

Expected Outcomes:
- Improved plantation survival
- Better environmental compliance
- Transparent monitoring
- Increased accountability
- Enhanced public participation

## 2. Features
- **GPS Geo-tagging:** Browser/mobile GPS capture with accuracy and altitude metadata.
- **Plantation Tracking:** Map-based interface (Esri World Imagery) with boundaries and markers.
- **Image Verification:** Gemini-powered AI analysis of site photos, location-gated by GPS.
- **Maintenance & Alerts:** Risk-linked tasks and dynamic alert generation.
- **Progress Analytics:** Dynamic Phase 9 risk engine and Sentinel-2 NDVI trend analysis.

## 3. Architecture

```text
Citizen / Officer
       │
       ▼
   Next.js Frontend
       │
       ▼
    FastAPI Backend
 ┌─────┼───────────────┐
 │     │               │
 ▼     ▼               ▼
GPS  Gemini       Risk Engine
 │                     │
 ▼                     ▼
PostGIS             Alerts
 │                     │
 └───────┬─────────────┘
         ▼
      Supabase
         │
         ▼
 Google Earth Engine
         │
         ▼
 Sentinel-2 → NDVI
```

## 4. Tech Stack
- **Frontend:** Next.js 14.2, React, TypeScript, Leaflet.
- **Backend:** FastAPI, Python, SQLAlchemy/GeoAlchemy2.
- **Database:** Supabase (PostgreSQL + PostGIS).
- **Integrations:** Google Earth Engine (Python API), Google Gemini API, Telegram API.

## 5. Repository Structure
- `/frontend`: Next.js application, React components, and styling (`globals.css`).
- `/backend`: FastAPI routers, services (NDVI, Risk, AI, Geo), and schemas.
- `/supabase`: (If applicable) Database migrations and configuration.

## 6. Setup and Local Running

### Database Setup
1. Create a Supabase project and enable the **PostGIS** extension.
2. Apply the necessary schema (Plantations, Field Visits, NDVI, Alerts).

### Backend Setup
1. Install Python dependencies: `pip install -r requirements.txt` (or via `uv/poetry` if used).
2. Configure environment variables (see `.env.example`).
3. Run the server: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Frontend Setup
1. Navigate to `frontend/`.
2. Install dependencies: `npm install`
3. Configure environment variables (see `frontend/.env.example`).
4. Run the development server: `npm run dev`

### Environment Variables
**Never commit `.env` or `.env.local` to version control.**
Review the provided `.env.example` files. You will need:
- Supabase URL & Anon Key
- Gemini API Key (Backend)
- Telegram Bot Token & Chat ID (Backend)
- Earth Engine Credentials (Backend)

### Google Earth Engine
- The backend NDVI service queries `COPERNICUS/S2_SR_HARMONIZED`.
- Requires an active GCP Project with the Earth Engine API enabled.
- Authentication happens via Service Account JSON or local `earthengine authenticate`.

## 7. Data Provenance & Real vs Demo Sites
**Rule: Never fabricate tree counts, planting dates, boundaries, or NDVI.**

### Real Verified Sites
- **MMRCL Compensatory Miyawaki (Goregaon):** 0.3 ha. MVP proxy boundary.
- **Smriti Van Urban Forest (Warje, Pune):** 18.99 ha. MVP proxy boundary.
*Note: Boundaries are currently proxy polygons, not official cadastral geometries.*

### Demo/Synthetic Sites
- **Nashik Hills Block A** & **Pune Western Ghats B**
*Note: Used strictly for regression testing, risk testing, and fallback demos. Do not represent these as real plantations.*

## 8. Current UI Status & Design Handoff
Vanadrishti's UI uses a strict design system intended to be observational, geographic, precise, institutional, calm, and modern. 
- **Stage A Foundation** is complete (Tokens, IBM Plex fonts, Shared Buttons, VanadrishtiMark).
- **Dashboard (Stage B)** is operational with map and alerts.
- **Remaining UI:** Further stages (Detail page, Citizen view, full Field UX) are pending for the next developer.

## 9. Known Limitations
- Proxy boundaries are not legal geometries.
- Optical satellite observations (Sentinel-2) may be unavailable during heavy cloud cover (handled gracefully as `null`).
- Current survival tree counts are intentionally excluded from the UI to preserve data integrity.
- Prototype MVP status.

## 10. Security Notes
- The Telegram Token was historically exposed but has been removed from the frontend. **Rotate your Telegram keys**.
- All secrets must reside exclusively in the backend environment.
- See `DEVELOPER_HANDOFF.md` for continuation details.

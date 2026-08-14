# Changelog

All notable changes to the Vanadrishti project will be documented in this file.

## [Unreleased]

### Added
- **Database Schema:** Defined the PostGIS and PostgreSQL Supabase schema for Plantations, Field Visits, Alerts, and NDVI tracking.
- **Geofence Engine:** Integrated PostGIS point-in-polygon logic with distance-to-boundary metrics.
- **Anti-Spoof:** Added server timestamps and heuristics to detect GPS manipulation.
- **Gemini Gating:** Field visit photos are now passed to Gemini AI for health verification, strictly gated by location confidence.
- **NDVI Processing:** Integrated Sentinel-2 via Google Earth Engine with monthly cloud-filtered aggregations and null handling.
- **Risk Engine:** Implemented Phase 9 dynamic scoring algorithm combining NDVI, AI, recency, maintenance, and trust inputs.
- **Site Classification:** Grouped sites into `real_verified` and `synthetic_demo`.
- **Goregaon Integration:** Mapped the MMRCL Compensatory Miyawaki proxy boundary.
- **Smriti Van Integration:** Mapped the Smriti Van Urban Forest proxy boundary.
- **UI Foundation:** Created `VanadrishtiMark`, integrated IBM Plex fonts, and built out color tokens.

### Fixed
- **Dashboard Recovery:** Successfully reverted unwanted generic UI layouts back to the approved functional grid/flex baseline (Stage B).
- **Marker Visibility:** Restored Leaflet SVG map markers with hardcoded hex colors, thick borders, and contrast halos to remain visible over Esri imagery.
- **Telegram Security:** Purged Telegram bot tokens and chat IDs from the frontend and local storage. Notification logic is now strictly backend-dependent.

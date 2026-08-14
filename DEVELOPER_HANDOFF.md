# Vanadrishti Developer Handoff

## READ THIS FIRST
Welcome to the Vanadrishti frontend team!
This project monitors compensatory afforestation using GPS, AI (Gemini), and Satellite GIS data (Sentinel-2 via Google Earth Engine). 
- **What's working:** Backend API, Supabase Database, Earth Engine NDVI pipelines, Gemini integrations, Risk Engine, and the core frontend Dashboard map (Stage B). 
- **What's fragile:** The Leaflet map integration is highly customized for Esri World Imagery with SVG string markers. Do NOT break the map rendering or introduce map libraries (like Mapbox) without authorization.
- **What must NOT be changed:** The API endpoints (`/plantations`, `/plantations/stats`, `/alerts`), the PostGIS architecture, and the dynamic risk scoring engine. Do not fabricate missing data (missing months must remain `null`).
- **Where to start:** Review this document and the design tokens in `frontend/app/globals.css`. Then proceed with the frontend roadmap below.

## Current UI State
- **Stage A Foundation** is complete (IBM Plex fonts, basic colors, button styles, badging).
- **Stage B (Officer Dashboard)** is implemented as a functional MVP.
- The final visual redesign is incomplete and awaits your touch.

## Protected Components
Treat these carefully:
1. `PlantationMap.tsx`: Handled dynamically, SVG markers must use hardcoded hex colors to be visible against Esri imagery.
2. `NDVIChart.tsx`: Handles nulls correctly. Do not interpolate missing data to `0`.
3. `api.ts`: API flow is strict.

## Frontend Roadmap (Recommended Order)
1. **Dashboard visual refinement**
2. **Map marker/popup polish** (Stage C)
3. **Plantation detail** (Stage D)
4. **Login/field** (Stage E)
5. **Citizen view** (Stage F)
6. **Mobile styling & Accessibility** (Stage G)
7. **Final E2E** (Stage H)

## Design References
The UI must feel: **Observational, Geographic, Precise, Institutional, Calm, Modern**.
- Use neutral backgrounds (`#F5F5F0`, `#FFFFFF`).
- Avoid an entirely "green" app. Green is a semantic signal (healthy), not a wallpaper.
- Avoid generic SaaS cards, giant emojis, or heavy glassmorphism.
- The Map is the anchor of the product.

## Testing Checklist
**Before making a PR:**
- [ ] Run `npm run build` and ensure Next.js typechecks pass.
- [ ] Verify `GET /plantations`, `GET /plantations/stats`, `GET /alerts` return 200.
- [ ] Verify 4 sites are visible on the map (Goregaon, Smriti Van, 2x Demos).
- [ ] Verify marker clicks trigger smooth `flyTo`.
- [ ] Ensure mobile widths (375px - 430px) do not overflow horizontally.

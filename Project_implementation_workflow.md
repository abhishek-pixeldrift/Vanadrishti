# **EcoTrack — AI/Vibe-Coding Implementation Procedure**

---

## **PHASE 1 — EXISTING PROJECT AUDIT**

**Step 1:** Ask Kiro to list the directory structure of the EcoTrack project starting from the parent folder.

**Step 2:** Inspect `frontend/` folder structure and identify existing routing structure (App Router vs Pages Router).

**Step 3:** Inspect `backend/` folder structure and list all existing routers, services, and database files.

**Step 4:** Check if Supabase connection exists in `backend/database/connection.py` or equivalent.

**Step 5:** Verify PostGIS extension is enabled in Supabase by running: `SELECT PostGIS_Version();` in Supabase SQL Editor.

**Step 6:** Inspect existing database schema — identify tables: `plantations`, `field_visits`, `ai_verifications`, `ndvi_observations`, `alerts`, `maintenance_tasks`.

**Step 7:** Verify if `plantation_boundaries` table exists with PostGIS geometry column.

**Step 8:** List existing map implementation files — search for `Leaflet`, `react-leaflet`, `OpenStreetMap`, or any map components.

**Step 9:** Inspect existing GPS capture logic in field capture page/component.

**Step 10:** Inspect existing AI verification flow — identify how Gemini is called and where results are stored.

**Step 11:** Check `.env.example` and `.env` for existing environment variables.

**Step 12:** Run `npm run build` in `frontend/` and confirm no TypeScript errors.

**Step 13:** Run `uvicorn main:app --reload` in `backend/` and confirm server starts without errors.

**Step 14:** Document findings in `AUDIT.md` — list working features, incomplete features, and files requiring modification.

**Step 15:** Commit current state: `git add -A && git commit -m "Audit checkpoint before Mapbox migration"`

---

## **PHASE 2 — MAPBOX MIGRATION**

**Step 16:** Create Mapbox account at mapbox.com and generate access token with scopes: `styles:read`, `fonts:read`, `datasets:read`.

**Step 17:** Add `NEXT_PUBLIC_MAPBOX_TOKEN=` to `frontend/.env.example`.

**Step 18:** Add actual token to `frontend/.env`.

**Step 19:** Add `NEXT_PUBLIC_MAPBOX_TOKEN` to `.gitignore` verification check.

**Step 20:** Install Mapbox GL JS: `cd frontend && npm install mapbox-gl @types/mapbox-gl`

**Step 21:** Install Mapbox GL CSS: verify `mapbox-gl/dist/mapbox-gl.css` will be imported.

**Step 22:** Identify existing dashboard map component file path.

**Step 23:** Give Kiro the task of backing up the existing map component to `components/map/OldMap.tsx.backup`.

**Step 24:** Give Kiro the task of creating `components/map/MapboxDashboard.tsx` with:

* Client component directive  
* Mapbox GL JS initialization  
* Center: `[73.85, 19.00]` (Maharashtra)  
* Style: `mapbox://styles/mapbox/satellite-streets-v12`  
* Zoom: 8  
* Pitch: 0  
* Container height: `600px`  
* 2D/3D toggle button

**Step 25:** Test Mapbox component renders in isolation at `/test-map` route.

**Step 26:** Verify satellite imagery loads correctly.

**Step 27:** Verify 3D toggle changes pitch to 60 degrees.

**Step 28:** Verify no console errors related to Mapbox token or missing assets.

**Step 29:** Commit: `git add -A && git commit -m "Add Mapbox GL JS dashboard map component"`

---

## **PHASE 3 — POSTGIS \+ MAHARASHTRA PLANTATION DATA**

**Step 30:** Verify `plantation_boundaries` table exists with schema:

id UUID PRIMARY KEY  
plantation\_id UUID REFERENCES plantations(id)  
boundary GEOGRAPHY(POLYGON, 4326\)  
created\_at TIMESTAMP

**Step 31:** If table missing, give Kiro the task of creating migration SQL file: `backend/database/migrations/001_add_plantation_boundaries.sql`.

**Step 32:** Run migration against Supabase.

**Step 33:** Verify existing `plantations` table has columns: `id`, `name`, `district`, `latitude`, `longitude`, `area_hectares`, `status`.

**Step 34:** Give Kiro the task of creating Python script: `backend/scripts/generate_boundaries.py` that:

* Reads 5 plantations from DB  
* Generates irregular polygons (12 points, 400–800m radius from centroid)  
* Outputs WKT format  
* Inserts into `plantation_boundaries` table

**Step 35:** Run `python backend/scripts/generate_boundaries.py`.

**Step 36:** Verify 5 boundaries inserted: `SELECT COUNT(*) FROM plantation_boundaries;`

**Step 37:** Query one boundary as GeoJSON: `SELECT ST_AsGeoJSON(boundary) FROM plantation_boundaries LIMIT 1;`

**Step 38:** Give Kiro the task of creating `backend/routers/boundaries.py` with endpoint: `GET /plantations/{id}/boundary` returning GeoJSON.

**Step 39:** Test endpoint with curl: `curl http://localhost:8000/plantations/{id}/boundary`

**Step 40:** Verify GeoJSON structure is valid.

**Step 41:** Commit: `git add -A && git commit -m "Add PostGIS plantation boundaries for Maharashtra sites"`

---

## **PHASE 4 — LOCATION VERIFICATION FOUNDATION**

**Step 42:** Give Kiro the task of creating `backend/services/geo_service.py` with stub functions:

* `validate_gps_metadata(coords: dict) -> dict`  
* `validate_point_in_boundary(lat: float, lng: float, plantation_id: str) -> dict`  
* `calculate_location_confidence(gps_data: dict, boundary_result: dict, spoof_result: dict) -> dict`

**Step 43:** Give Kiro the task of creating `backend/services/anti_spoof_service.py` with stub function:

* `calculate_spoof_risk(submission: dict, user_history: list) -> dict`

**Step 44:** Inspect existing `field_visits` table schema.

**Step 45:** Add GPS metadata columns if missing:

* `gps_accuracy FLOAT`  
* `gps_altitude FLOAT`  
* `gps_heading FLOAT`  
* `gps_speed FLOAT`  
* `client_timestamp TIMESTAMP`  
* `server_timestamp TIMESTAMP`  
* `user_agent TEXT`  
* `location_confidence JSONB`

**Step 46:** Run migration to add columns.

**Step 47:** Give Kiro the task of updating `backend/models/schemas.py` Pydantic model `FieldVisit` with new GPS fields.

**Step 48:** Update `frontend/lib/types.ts` TypeScript interface `FieldVisit` to match.

**Step 49:** Commit: `git add -A && git commit -m "Add location verification foundation and GPS metadata schema"`

---

## **PHASE 5 — M6A GPS CAPTURE**

**Step 50:** Inspect existing field capture page — identify file path (e.g., `app/field/page.tsx` or `components/field/FieldCapture.tsx`).

**Step 51:** Give Kiro the task of creating `components/field/GpsCapture.tsx` client component with:

* `navigator.geolocation.getCurrentPosition` with `enableHighAccuracy: true`  
* Display: latitude, longitude, accuracy, altitude, timestamp  
* Color-coded accuracy: green (≤50m), amber (51–100m), red (\>100m)  
* "Retrying GPS..." state while accuracy \> 100m  
* Auto-retry every 3 seconds, max 5 attempts  
* Manual "Retry GPS" button  
* Warning banner if accuracy \> 50m

**Step 52:** Integrate `GpsCapture` component into existing field capture form.

**Step 53:** Disable form submit button until GPS acquired (accuracy present and ≤ 500m).

**Step 54:** Test on desktop browser — verify amber/red accuracy and warning banner.

**Step 55:** Test on mobile device outdoors — verify green accuracy achieved.

**Step 56:** Inspect existing `POST /field-visits` endpoint in `backend/routers/field_visits.py`.

**Step 57:** Give Kiro the task of modifying `POST /field-visits` to:

* Accept all GPS metadata fields in request body  
* Call `geo_service.validate_gps_metadata(coords)`  
* Reject if accuracy \> 500m  
* Store `server_timestamp` as current UTC time  
* Store all GPS fields in database

**Step 58:** Test GPS capture → form submit → verify GPS data stored in `field_visits` table.

**Step 59:** Verify no console errors during GPS capture.

**Step 60:** Commit: `git add -A && git commit -m "Implement M6A GPS capture with accuracy feedback"`

---

## **PHASE 6 — M6B GEOFENCE \+ ANTI-SPOOFING**

**Step 61:** Give Kiro the task of implementing `geo_service.validate_point_in_boundary`:

* Create PostGIS function `check_point_in_plantation` in Supabase  
* Use `ST_Contains` for inside check  
* Use `ST_Distance` for distance calculation  
* Return: `inside: bool`, `distance_meters: float`

**Step 62:** Run PostGIS function creation SQL in Supabase SQL Editor.

**Step 63:** Test function manually: `SELECT * FROM check_point_in_plantation(ST_GeogFromText('POINT(73.7919 20.0035)'), 'plantation-id');`

**Step 64:** Give Kiro the task of implementing Python wrapper in `geo_service.py` that calls Supabase RPC.

**Step 65:** Test endpoint: create test route `GET /test/geofence?lat=20.0035&lng=73.7919&plantation_id=xxx`

**Step 66:** Verify inside/outside result matches expected boundary.

**Step 67:** Give Kiro the task of implementing `anti_spoof_service.calculate_spoof_risk` with heuristics:

* Impossible travel (\>200 km/h from last submission)  
* Perfect accuracy (\<3m)  
* Timestamp drift (\>60s between client and server)  
* Duplicate coordinates

**Step 68:** Give Kiro the task of implementing `geo_service.calculate_location_confidence` with weighted scoring:

* GPS accuracy ≤50m: 30 points  
* Inside geofence: 40 points  
* No spoof flags: 20 points  
* Reasonable altitude: 10 points

**Step 69:** Give Kiro the task of modifying `POST /field-visits` to:

* Call `validate_point_in_boundary` after GPS validation  
* Call `calculate_spoof_risk` with user submission history  
* Call `calculate_location_confidence`  
* Store result in `location_confidence` JSONB column  
* If confidence \< 40, set `status='flagged_location'` and skip AI verification  
* If confidence ≥ 40, proceed to AI verification

**Step 70:** Add small Mapbox map to field capture form showing:

* Selected plantation boundary as blue polygon  
* User GPS point as red marker  
* "Inside boundary" / "Outside boundary" status message

**Step 71:** Test submission inside boundary → verify HIGH confidence, proceeds to AI.

**Step 72:** Test submission outside boundary → verify LOW confidence, flagged for review.

**Step 73:** Test impossible travel heuristic by manually creating two submissions 500km apart within 1 hour.

**Step 74:** Verify spoof flags appear in `location_confidence` JSON.

**Step 75:** Commit: `git add -A && git commit -m "Implement M6B geofence validation and anti-spoofing"`

---

## **PHASE 7 — GEMINI GATED VERIFICATION**

**Step 76:** Inspect existing AI verification implementation in `backend/services/ai_service.py`.

**Step 77:** Verify `GEMINI_API_KEY` exists in `backend/.env`.

**Step 78:** Give Kiro the task of modifying `POST /field-visits` AI verification logic:

* Check `location_confidence['confidence_level']`  
* If `'LOW'`, skip Gemini call, return early with status `'pending_location_review'`  
* If `'MEDIUM'` or `'HIGH'`, proceed to Gemini verification

**Step 79:** Give Kiro the task of adding location gate response to API:

{  
  "status": "pending\_location\_review",  
  "location\_confidence": { ... },  
  "ai\_result": null,  
  "message": "Location confidence too low — flagged for officer review"  
}

**Step 80:** Test submission with LOW location confidence → verify Gemini NOT called, status is `pending_location_review`.

**Step 81:** Test submission with HIGH location confidence → verify Gemini called, AI result returned.

**Step 82:** Inspect existing frontend AI result display component.

**Step 83:** Give Kiro the task of updating AI result component to show:

* If `status === 'pending_location_review'`: show location warning message instead of AI result  
* If AI result present: show tree detected, health assessment, confidence

**Step 84:** Test full flow: bad GPS → location flagged → no AI result shown.

**Step 85:** Test full flow: good GPS → location passes → AI result shown.

**Step 86:** Commit: `git add -A && git commit -m "Gate Gemini verification behind location confidence threshold"`

---

## **PHASE 8 — NDVI FAST MODE**

**Step 87:** Verify `ndvi_observations` table exists with columns: `id`, `plantation_id`, `observation_date`, `ndvi_value`, `health_status`, `data_source`.

**Step 88:** Verify seed data exists: `SELECT COUNT(*) FROM ndvi_observations;` (should be \~60 rows for 5 plantations × 12 months).

**Step 89:** Inspect existing `backend/services/ndvi_service.py`.

**Step 90:** Give Kiro the task of implementing `get_ndvi_observations(plantation_id: str, source: str = 'seed')` that queries `ndvi_observations` WHERE `data_source = 'seed'`.

**Step 91:** Give Kiro the task of creating `GET /ndvi/{plantation_id}` endpoint in `backend/routers/ndvi.py`.

**Step 92:** Test endpoint: `curl http://localhost:8000/ndvi/{plantation-id}`

**Step 93:** Verify 12 observations returned with dates and NDVI values.

**Step 94:** Inspect existing plantation detail page (e.g., `app/plantations/[id]/page.tsx`).

**Step 95:** Give Kiro the task of installing Recharts: `cd frontend && npm install recharts`

**Step 96:** Give Kiro the task of creating `components/charts/NdviChart.tsx` with:

* Recharts `LineChart`  
* X-axis: observation\_date  
* Y-axis: ndvi\_value (domain: \[0, 1\])  
* Reference lines at 0.3 (critical) and 0.6 (healthy)  
* Responsive container

**Step 97:** Integrate `NdviChart` into plantation detail page.

**Step 98:** Test detail page for Plantation "Sahyadri Range West C" — verify declining NDVI trend visible.

**Step 99:** Test detail page for Plantation "Satara Plateau D" — verify recovery curve visible.

**Step 100:** Give Kiro the task of adding health trend label logic:

* Compare last 3 NDVI observations  
* If increasing: "Improving"  
* If flat: "Stable"  
* If decreasing: "Declining"

**Step 101:** Verify health trend label displays correctly on all 5 plantation detail pages.

**Step 102:** Commit: `git add -A && git commit -m "Implement NDVI Fast Mode with Recharts visualization"`

---

## **PHASE 9 — RISK \+ ALERTS \+ TELEGRAM**

**Step 103:** Inspect existing `backend/services/risk_engine.py`.

**Step 104:** Give Kiro the task of implementing `calculate_risk_score(plantation_id: str)` with weighted inputs:

* NDVI trend (last 3 obs): 35 points  
* AI health assessment: 25 points  
* Days since last visit: 20 points  
* Maintenance history: 10 points  
* Location confidence: 10 points

**Step 105:** Give Kiro the task of implementing risk level classification:

* HIGH: ≥60  
* MEDIUM: 40–59  
* LOW: \<40

**Step 106:** Give Kiro the task of creating `GET /risk/{plantation_id}` endpoint.

**Step 107:** Test risk endpoint for Plantation "Sahyadri Range West C" — verify HIGH risk score.

**Step 108:** Give Kiro the task of modifying `POST /field-visits` to call `risk_engine.calculate_risk_score` after AI verification completes.

**Step 109:** Verify `alerts` table exists with columns: `id`, `plantation_id`, `alert_type`, `severity`, `message`, `created_at`, `acknowledged`.

**Step 110:** Give Kiro the task of implementing alert auto-generation:

* If risk score ≥ 60 AND no unacknowledged alert exists for plantation  
* Create alert with `severity='HIGH'`, `alert_type='risk_threshold'`

**Step 111:** Create Telegram bot via BotFather and get bot token.

**Step 112:** Add `TELEGRAM_BOT_TOKEN=` and `TELEGRAM_CHAT_ID=` to `backend/.env.example`.

**Step 113:** Add actual values to `backend/.env`.

**Step 114:** Give Kiro the task of creating `backend/services/notify_service.py` with function `send_telegram(message: str)` that:

* Uses `requests.post` to Telegram Bot API  
* Wraps in try/except, returns success/failure boolean  
* Logs error but does not raise exception on failure

**Step 115:** Give Kiro the task of modifying alert auto-generation to call `notify_service.send_telegram` when HIGH alert created.

**Step 116:** Test alert flow: submit field visit → risk recalculates → HIGH risk → alert created → Telegram message sent.

**Step 117:** Verify Telegram message received on demo phone.

**Step 118:** Test Telegram failure fallback: set invalid bot token, verify system does not crash.

**Step 119:** Verify `maintenance_tasks` table exists with columns: `id`, `plantation_id`, `alert_id`, `problem`, `risk_level`, `recommended_action`, `assigned_to`, `due_date`, `status`.

**Step 120:** Give Kiro the task of creating `POST /maintenance` endpoint to create task from alert.

**Step 121:** Give Kiro the task of creating `PATCH /maintenance/{id}/status` endpoint to update task status.

**Step 122:** Commit: `git add -A && git commit -m "Implement risk engine, alert auto-generation, and Telegram notifications"`

---

## **PHASE 10 — OFFICER REVIEW**

**Step 123:** Inspect existing officer dashboard page (e.g., `app/dashboard/page.tsx`).

**Step 124:** Give Kiro the task of creating `GET /alerts` endpoint returning all alerts ordered by severity DESC, created\_at DESC.

**Step 125:** Give Kiro the task of creating alerts feed component on dashboard:

* Table with columns: Plantation, Severity, Message, Created At  
* Severity badge with color: HIGH=red, MEDIUM=amber, LOW=gray

**Step 126:** Verify alerts feed displays seeded/auto-generated alerts.

**Step 127:** Give Kiro the task of creating `GET /maintenance` endpoint returning all maintenance tasks.

**Step 128:** Give Kiro the task of creating maintenance task table component on dashboard:

* Columns: Plantation, Problem, Risk Level, Assignee, Due Date, Status, Actions  
* "Mark Complete" button per task

**Step 129:** Wire "Mark Complete" button to `PATCH /maintenance/{id}/status` with `status='completed'`.

**Step 130:** Test mark complete → verify status updates in table.

**Step 131:** Give Kiro the task of creating `GET /submissions/flagged` endpoint returning field visits WHERE `location_confidence['confidence_level'] = 'LOW'` OR `location_confidence['confidence_level'] = 'MEDIUM'`.

**Step 132:** Give Kiro the task of creating flagged submissions table component on dashboard:

* Columns: Citizen, Plantation, GPS Accuracy, Inside Boundary, Spoof Risk, Actions  
* "Review" button per row

**Step 133:** Give Kiro the task of creating location review modal component with:

* Mapbox map showing plantation boundary \+ submitted GPS point  
* Location confidence breakdown (accuracy, geofence, spoof flags)  
* "Approve" and "Reject" buttons

**Step 134:** Give Kiro the task of creating `PATCH /field-visits/{id}/review-location` endpoint:

* Sets `location_approved: true/false`  
* If approved: triggers AI verification (if not already done)  
* If rejected: sets status to `'rejected'`, calls `notify_service.send_telegram` to citizen

**Step 135:** Wire modal buttons to review endpoint.

**Step 136:** Test flagged submission review flow: flag appears → click Review → modal opens → map shows boundary \+ point → Approve → AI verification runs.

**Step 137:** Test reject flow: Reject → status updated → Telegram notification sent.

**Step 138:** Commit: `git add -A && git commit -m "Implement officer review dashboard with flagged submissions and location review modal"`

---

## **PHASE 11 — CITIZEN EXPERIENCE**

**Step 139:** Inspect existing citizen portal page (e.g., `app/portal/page.tsx`).

**Step 140:** Give Kiro the task of creating `GET /submissions?citizen={username}` endpoint returning field visits filtered by `worker_name`.

**Step 141:** Give Kiro the task of creating submissions table component on citizen portal:

* Columns: Plantation, Submission Date, GPS Accuracy, Status, AI Result Summary  
* Status badge: Pending=gray, Approved=green, Rejected=red, Flagged=amber

**Step 142:** Wire table to `GET /submissions` endpoint.

**Step 143:** Test citizen login → portal shows their submissions with correct statuses.

**Step 144:** Give Kiro the task of adding "New Submission" button on portal linking to `/field`.

**Step 145:** Give Kiro the task of ensuring field capture page pre-fills plantation dropdown if `?plantation_id=xxx` query param present.

**Step 146:** Test "Submit Evidence" link from plantation detail → field page opens with plantation pre-selected.

**Step 147:** Commit: `git add -A && git commit -m "Implement citizen portal with submission history"`

---

## **PHASE 12 — 2D/3D GIS DASHBOARD INTEGRATION**

**Step 148:** Give Kiro the task of modifying `components/map/MapboxDashboard.tsx` to accept `plantations` prop.

**Step 149:** Give Kiro the task of adding plantation markers to map:

* Color by status: healthy=green, warning=amber, critical=red  
* Popup on click showing name, status, "View Details" link

**Step 150:** Give Kiro the task of loading plantation boundaries as GeoJSON layers:

* Fetch `GET /plantations/{id}/boundary` for each plantation  
* Add as filled polygon with 0.2 opacity  
* Add outline with 2px width  
* Match boundary color to marker color

**Step 151:** Give Kiro the task of adding 3D terrain source:

* `mapbox-dem` from `mapbox://mapbox.mapbox-terrain-dem-v1`  
* `setTerrain` with `exaggeration: 1.5`

**Step 152:** Give Kiro the task of implementing "Toggle 3D" button:

* Click → pitch changes from 0° to 60° with easeToanimation  
* Button label changes: "View 3D" / "View 2D"

**Step 153:** Wire `MapboxDashboard` into officer dashboard page with `plantations` data from `GET /plantations`.

**Step 154:** Test 2D view: all 5 plantations visible with markers and boundaries.

**Step 155:** Test 3D toggle: map tilts to 60°, terrain elevation visible.

**Step 156:** Test marker popup: click Plantation "Sahyadri Range West C" → popup shows name and status → "View Details" link works.

**Step 157:** Verify map container does NOT take over entire viewport — height constrained to 600px, dashboard stats/alerts visible above/below.

**Step 158:** Commit: `git add -A && git commit -m "Integrate Mapbox 2D/3D GIS into officer dashboard with plantation markers and boundaries"`

---

## **PHASE 13 — LAPTOP \+ MOBILE RESPONSIVE VALIDATION**

**Step 159:** Test officer dashboard on 1280px laptop screen:

* Map renders correctly within container  
* Stat cards visible above map  
* Alerts feed and maintenance tasks visible below map  
* No horizontal scroll

**Step 160:** Test officer dashboard on 1920px desktop screen:

* Layout does not break  
* Map scales appropriately

**Step 161:** Test citizen portal on mobile (375px width):

* GPS capture component usable  
* Form fields stack vertically  
* Submit button accessible  
* Map (if present) does not overflow

**Step 162:** Test field capture page on mobile outdoors:

* GPS acquires lock within 15 seconds  
* Accuracy displays as green (≤50m)  
* Photo upload works via camera capture  
* Form submits successfully

**Step 163:** Give Kiro the task of adding Tailwind responsive classes to map container:

* `h-[400px] md:h-[600px]` for height  
* `w-full` for width

**Step 164:** Give Kiro the task of adding responsive breakpoints to dashboard grid:

* Stat cards: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`  
* Alerts/tasks: `grid-cols-1 lg:grid-cols-2`

**Step 165:** Test all responsive breakpoints: 375px, 768px, 1024px, 1280px, 1920px.

**Step 166:** Fix any layout breaks identified during testing.

**Step 167:** Commit: `git add -A && git commit -m "Ensure responsive layout for laptop and mobile"`

---

## **PHASE 14 — END-TO-END INTEGRATION**

**Step 168:** Clear browser localStorage.

**Step 169:** Restart both dev servers.

**Step 170:** Execute golden path as officer:

* Login with officer credentials  
* Dashboard loads with 5 plantations on map  
* Click Plantation "Sahyadri Range West C" marker  
* Popup appears with correct status (Critical)  
* Click "View Details" in popup  
* Plantation detail page loads  
* NDVI chart shows declining trend  
* Risk score shows HIGH  
* Navigate back to dashboard

**Step 171:** Execute golden path as citizen (mobile device preferred):

* Login with citizen credentials  
* Portal loads with submission history (if seeded)  
* Click "New Submission"  
* Field capture page loads  
* Select "Sahyadri Range West C" from dropdown  
* GPS captures coordinates (green accuracy on mobile)  
* Map shows boundary and user pin inside boundary  
* Upload tree photo  
* Click Submit  
* Location confidence calculates → HIGH  
* AI verification runs → result displays  
* Submission complete message shown

**Step 172:** Return to officer dashboard:

* Risk recalculation triggered  
* HIGH risk maintained  
* New alert auto-generated  
* Alert appears in alerts feed  
* Telegram notification received (if configured)

**Step 173:** Officer creates maintenance task from alert:

* Click "Create Task" on alert  
* Task form pre-filled with plantation and alert details  
* Submit task  
* Task appears in maintenance tasks table

**Step 174:** Officer marks task complete:

* Click "Mark Complete" on task  
* Status updates to Completed  
* Alert acknowledged

**Step 175:** Officer reviews flagged submission (if any exist):

* Navigate to Flagged Submissions table  
* Click "Review" on a submission  
* Modal opens with map showing boundary \+ GPS point  
* Location confidence breakdown visible  
* Click "Approve"  
* AI verification runs (if gated)  
* Status updates

**Step 176:** Document any broken steps in `INTEGRATION_ISSUES.md`.

**Step 177:** Fix critical issues blocking the golden path.

**Step 178:** Re-run golden path end-to-end without errors.

**Step 179:** Commit: `git add -A && git commit -m "End-to-end integration verified - golden path complete"`

---

## **PHASE 15 — TESTING \+ DEMO PREPARATION**

**Step 180:** Give ChatGPT the task of listing all edge cases that should be tested.

**Step 181:** Test edge case: GPS timeout (disable location services) → verify graceful error message shown.

**Step 182:** Test edge case: Gemini API failure (set invalid API key) → verify fallback response, form does not crash.

**Step 183:** Test edge case: Submission with perfect accuracy (0m) → verify spoof flag triggered.

**Step 184:** Test edge case: Submission outside all plantation boundaries → verify auto-reject.

**Step 185:** Test edge case: 3D map toggle during data loading → verify no crash.

**Step 186:** Test edge case: Mapbox token invalid → verify error message, map does not break page layout.

**Step 187:** Give Kiro the task of adding loading states to:

* Dashboard map (skeleton or spinner while tiles load)  
* NDVI chart (loading spinner)  
* GPS capture ("Acquiring GPS..." message)  
* Form submission ("Submitting..." disabled button state)

**Step 188:** Give Kiro the task of adding error states to:

* Map load failure (show error message in map container)  
* API failures (show inline error alert, not blank page)  
* GPS unavailable (show error with retry instructions)

**Step 189:** Give Kiro the task of ensuring consistent status badge colors across all views:

* Healthy: green  
* Warning: amber  
* Critical: red  
* Pending: gray  
* Approved: green  
* Rejected: red  
* Flagged: amber

**Step 190:** Run frontend build: `npm run build` → verify no TypeScript errors.

**Step 191:** Run backend tests (if implemented): `pytest` → verify no failures.

**Step 192:** Test on actual demo device (laptop \+ mobile):

* Confirm screen resolution matches demo projector/screen  
* Test actual browser that will be used (Chrome recommended)  
* Confirm internet connection stable

**Step 193:** Pre-seed one HIGH-risk plantation with complete history (NDVI decline, field visits, AI results, alert, maintenance task) for reliable demo.

**Step 194:** Take screenshots of each golden path step for backup slides (in case of internet failure).

**Step 195:** Write demo script in `DEMO_SCRIPT.md` with exact click-by-click instructions.

**Step 196:** Rehearse demo 3 times, time it (target: 2.5 minutes).

**Step 197:** Commit: `git add -A && git commit -m "Testing complete - demo ready"`

---

## **PHASE 16 — GITHUB FINALIZATION**

**Step 198:** Give Kiro the task of updating `README.md` with:

* Project overview  
* Tech stack  
* Setup instructions (install, env vars, seed data, run commands)  
* Demo golden path steps  
* Known limitations (GPS accuracy, mock NDVI, no auth)  
* Future roadmap (live GEE, production auth, offline sync)

**Step 199:** Verify `.env.example` contains all required keys with placeholder values.

**Step 200:** Verify `.gitignore` contains:

* `.env`  
* `node_modules/`  
* `.next/`  
* `__pycache__/`  
* `*.pyc`  
* `*.log`

**Step 201:** Create `LICENSE` file (MIT recommended for hackathon projects).

**Step 202:** Run final commit: `git add -A && git commit -m "Final commit - EcoTrack MVP complete"`

**Step 203:** Push to GitHub: `git push origin main`

**Step 204:** Create GitHub release: tag `v1.0.0-mvp`, title "EcoTrack 2-Day MVP", include demo script in release notes.

**Step 205:** Verify repository is public and all files pushed correctly.

**Step 206:** Clone repository in a fresh directory and run setup instructions from README to verify they work.

**Step 207:** Deploy backend to a hosting service (optional, if demo requires public URL): Render, Railway, or Heroku.

**Step 208:** Deploy frontend to Vercel or Netlify (optional, if demo requires public URL).

**Step 209:** If deployed, test deployed URLs and update README with live demo link.

**Step 210:** Finalization complete — project ready for demo.

---

**END OF PROCEDURE**

Q-eSfCi&bWbc5*/


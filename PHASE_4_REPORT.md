# Phase 4 — Web Dashboard Report

**Project:** Hindsight-Powered Incident Response Agent  
**Phase:** 4 — Web Dashboard (React + Vite + TypeScript)  
**Date:** September 28, 2026  
**Status:** **Complete**

---

## 1. Status

**Complete**

A modern, functional, SRE operations dashboard built with React 18, Vite 6, and TypeScript has been implemented in the `frontend/` directory. It communicates directly with the Phase 1–3 FastAPI backend, renders deterministic telemetry signals, faithfully reports Hindsight connectivity, provides ranked hypotheses, diagnostic investigation steps, and remediation recommendations, and includes 25 passing frontend unit/integration tests alongside the 51 passing backend tests (76 total passing automated tests).

---

## 2. Frontend Structure

```
frontend/
├── .env                              # Local environment configuration
├── .env.example                      # Reference environment template
├── package.json                      # Dependencies and scripts (dev, build, preview, test)
├── tsconfig.json                     # Strict TypeScript compiler options
├── tsconfig.node.json                # Vite configuration TypeScript options
├── vite.config.ts                    # Vite config with proxy to http://127.0.0.1:8000 & Vitest config
├── index.html                        # Application entrypoint with Inter and JetBrains Mono typography
├── src/
│   ├── api/
│   │   └── client.ts                 # Strongly typed HTTP client using Fetch API
│   ├── types/
│   │   ├── incident.ts               # Incident, Severity, IncidentStatus, IncidentCreate, IncidentResolve
│   │   ├── investigation.ts          # InvestigationResult, ObservedSignals, Hypotheses, RemediationPlan
│   │   ├── hindsight.ts              # HindsightConnectionStatus, BackendHealth
│   │   └── index.ts                  # Centralized type exports
│   ├── components/
│   │   ├── Header.tsx                # App banner, API status, Hindsight status indicator, Refresh, New Incident
│   │   ├── IncidentList.tsx          # Incident sidebar list with search, status & severity filters
│   │   ├── IncidentDetail.tsx        # Incident pane with tabbed views, metadata, and "Investigate Incident" CTA
│   │   ├── InvestigationView.tsx     # Comprehensive InvestigationResult rendering across 6 sections
│   │   ├── SeverityBadge.tsx         # Color-coded badge for CRITICAL, HIGH, MEDIUM, LOW
│   │   ├── StatusBadge.tsx           # Color-coded badge for OPEN, INVESTIGATING, RESOLVED
│   │   ├── CreateIncidentModal.tsx   # Modal for reporting new incidents to the backend
│   │   └── ResolveModal.tsx          # Modal for recording postmortem root cause and applied mitigation
│   ├── __tests__/
│   │   ├── IncidentList.test.tsx     # 6 unit tests (rendering, search, status filtering, selection)
│   │   ├── IncidentDetail.test.tsx   # 7 unit tests (overview telemetry, loading state, investigate CTA)
│   │   ├── InvestigationView.test.tsx# 8 unit tests (signals, hypotheses, Hindsight online/offline, remediation)
│   │   └── App.test.tsx              # 4 integration tests (health check, offline banner, error boundary)
│   ├── test-setup.ts                 # Vitest jsdom setup and @testing-library/jest-dom integration
│   ├── index.css                     # SRE dark-mode design system with CSS custom properties
│   ├── App.tsx                       # Main dashboard state machine, auto-selection, error banners
│   └── main.tsx                      # React root mounter
├── scripts/
│   └── capture_screenshots.js        # Automated headless browser verification and screenshot engine
└── dist/                             # Optimized production build bundle
```

---

## 3. Components Created

| Component | Responsibility |
|---|---|
| `Header` | Displays brand name ("Incident Response Agent / Hindsight SRE"), live backend status pill (green/red dot), live Hindsight connection status pill, manual refresh trigger, and modal trigger for reporting incidents. |
| `IncidentList` | Left-hand navigation sidebar. Supports real-time client-side full-text search across incident ID, title, and affected service. Features dropdown filters for Status (`all`, `open`, `investigating`, `resolved`) and Severity (`all`, `critical`, `high`, `medium`, `low`). |
| `IncidentDetail` | Main incident workspace pane. Displays header metadata (ID, title, severity, status, service, timestamps), action buttons ("Resolve", "Investigate Incident"), and tab navigation between **Agent Investigation** and **Overview & Raw Telemetry**. |
| `InvestigationView` | Dedicated investigation renderer covering all fields of `InvestigationResult`: Executive Summary banner with confidence percentage, Observed Signals grid, Hindsight Memory Context, Ranked Hypotheses, Diagnostic Steps, Remediation Recommendations, and Caveats. |
| `SeverityBadge` | SRE-styled pill with clear visual distinctions for `critical` (crimson), `high` (orange), `medium` (amber), and `low` (slate). |
| `StatusBadge` | Operational indicator for `open` (blue), `investigating` (purple pulse), and `resolved` (emerald green). |
| `CreateIncidentModal` | Accessible dialog for submitting new incidents with title, service, severity, description, error messages, and raw logs. |
| `ResolveModal` | Accessible dialog requiring root cause and applied mitigation to resolve an active incident. |

---

## 4. API Integration

The frontend integrates directly with the Phase 1–3 FastAPI backend (`http://127.0.0.1:8000`) without duplicating backend business logic:

| HTTP Method | Backend Route | Frontend Client Function | Description |
|---|---|---|---|
| `GET` | `/health` | `api.getHealth()` | Verifies FastAPI connectivity and runtime health |
| `GET` | `/api/v1/hindsight/status` | `api.getHindsightStatus()` | Probes Hindsight memory service availability and bank configuration |
| `GET` | `/api/v1/incidents` | `api.getIncidents(filters)` | Retrieves list of all active/historical incidents |
| `GET` | `/api/v1/incidents/{incident_id}` | `api.getIncident(id)` | Retrieves detailed incident record including telemetry |
| `POST` | `/api/v1/incidents/{incident_id}/investigate` | `api.investigateIncident(id)` | Triggers AI Incident Response Agent investigation pipeline |
| `POST` | `/api/v1/incidents` | `api.createIncident(payload)` | Creates and seeds a new incident |
| `PATCH` | `/api/v1/incidents/{incident_id}` | `api.updateIncident(id, payload)`| Updates incident metadata |
| `POST` | `/api/v1/incidents/{incident_id}/resolve` | `api.resolveIncident(id, payload)`| Resolves incident with postmortem root cause & mitigation |

---

## 5. Investigation UI

When the on-call engineer clicks **"Investigate Incident"**, the dashboard calls `POST /api/v1/incidents/{incident_id}/investigate` and renders the structured `InvestigationResult`:

1. **Executive Summary:** Highlighted banner displaying high-level synthesized explanation along with an overall investigation confidence pill (e.g., `Confidence: 80%`).
2. **Observed Signals (Deterministic Telemetry Analysis):**
   - **Subsystems Involved:** Tag cloud isolating affected components (e.g., `connection pool`, `payment gateway`, `tls certificate`).
   - **Classified Error Patterns:** Red-bordered tags displaying parsed error classes (e.g., `Read Timeout`, `Connection Pool Exhaustion`).
   - **Suspected Outage Categories:** Categorical classification tags (e.g., `Database Connection Pool Exhaustion`, `API Latency & Timeout Spike`).
   - **Deployment Correlation:** Clear indicator showing whether the failure onset aligns with a recent release or deployment event.
   - **Extracted Signal Keywords:** Technical tokens extracted from stack traces.
3. **Historical Context:** Dedicated memory container (details in Section 6).
4. **Ranked Hypotheses:** Ordered cards clearly labelled as **Hypotheses** (*"Hypotheses require empirical verification; not confirmed root causes"*) rather than confirmed root causes:
   - Rank and hypothesis statement.
   - Per-hypothesis confidence score pill.
   - Bulleted list of **Supporting Evidence**.
   - Bulleted list of **Contradicting / Counter Evidence**.
   - Associated historical precedent tags if available.
5. **Recommended Non-Destructive Diagnostic Steps:** Ordered step-by-step diagnostic actions including rationale and target observability system (e.g., APM / Prometheus Metrics, PostgreSQL Primary).
6. **Remediation Recommendations:** Dual-column operational matrix separating **Immediate Mitigation (Stop Impact)** from **Long-Term Fixes (Prevent Recurrence)**. Neither button executes destructive actions; all items are informational recommendations.
7. **Investigation Caveats & Limitations:** Transparent disclosure of heuristic-only reasoning when Hindsight or LLM providers are offline.

---

## 6. Hindsight Display

Per the Phase 4 specification:
- **Zero Fabrication:** The frontend does not fabricate or hallucinate historical memories when the Hindsight service is unavailable.
- **Offline Representation:** When Hindsight is disconnected, the status badge prominently displays `HINDSIGHT OFFLINE` (crimson), and renders the warning banner:
  > *"Historical context unavailable — Hindsight memory service is currently disconnected. Investigation based solely on current telemetry."*
- **Online Representation:** When Hindsight is connected, the badge displays `HINDSIGHT ONLINE` (purple), shows the semantic query string used (`Query: "Find historical incidents..."`), lists recalled matching incidents with similarity scores and summaries, and renders the synthesized `Hindsight REFLECT Comparative Synthesis`.

---

## 7. Error Handling

| Scenario | UI Behavior |
|---|---|
| **Backend Offline / Network Failure** | Displays prominent top warning banner (`Backend Disconnected: Cannot connect to backend API server at http://127.0.0.1:8000`) with a "Retry Connection" button. |
| **Hindsight Disconnected** | Header indicator shows `Hindsight: Offline` with tooltip; investigation view clearly discloses offline state without failing the rest of the investigation. |
| **Investigation Failure** | In-panel critical error alert displaying the backend error message without exposing raw Python tracebacks; allows re-triggering. |
| **Empty Incident List** | Clean empty state with search icon and message *"No incidents found. Try adjusting your search or filter options."* |
| **Incident Not Found** | Sidebar selection falls back gracefully; empty state prompts selection of an available incident. |

---

## 8. CORS & Configuration

- **Frontend Configuration (`frontend/.env` & `frontend/.env.example`):**
  ```env
  VITE_API_BASE_URL="http://127.0.0.1:8000"
  ```
  Vite also defines proxy rules in `vite.config.ts` mapping `/api` and `/health` to `http://127.0.0.1:8000`.
- **Backend CORS Configuration (`backend/app/core/config.py` & `backend/.env`):**
  ```env
  CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
  ```
  Verified with HTTP `OPTIONS` preflight tests returning `HTTP/1.1 200 OK` and `access-control-allow-origin: http://127.0.0.1:5173`.

---

## 9. Automated Testing Results

### Backend Automated Tests
- **Command:** `..\.venv\Scripts\python.exe -m pytest -v`
- **Result:** **51 passed, 1 warning in 11.05s**
- **Suite Coverage:** Deterministic analysis, Hindsight client & memory, agent core reasoning pipeline, incident domain schemas, in-memory repository CRUD & filters, seed data validation, API endpoints (`GET /api/v1/incidents`, `POST /api/v1/incidents/{id}/investigate`, `/health`, `/api/v1/hindsight/status`).

### Frontend Automated Tests
- **Command:** `npm test` (Vitest v5.0.2 in `frontend/`)
- **Result:** **25 passed across 4 test files in 1.78s**
  - `src/__tests__/IncidentList.test.tsx` (6 passed)
  - `src/__tests__/InvestigationView.test.tsx` (8 passed)
  - `src/__tests__/IncidentDetail.test.tsx` (7 passed)
  - `src/__tests__/App.test.tsx` (4 passed)

### Production Build Verification
- **Command:** `npm run build`
- **Result:** TypeScript check (`tsc`) succeeded with 0 errors; Vite bundled `dist/assets/index-DIsIEPLo.js` (191 kB) and `dist/assets/index-B0Jhim_d.css` (13.6 kB) in 1.36s.

---

## 10. Manual & Live Verification

| Verification Step | Status | Evidence |
|---|---|---|
| Backend started? | **YES** | Uvicorn running on `http://127.0.0.1:8000`, 10 seed incidents loaded |
| Frontend started? | **YES** | Vite dev server running on `http://127.0.0.1:5173` |
| Incident list loaded? | **YES** | 10 incidents rendered in sidebar with badges and timestamps |
| Incident detail loaded? | **YES** | Title, metadata, raw logs, and error messages rendered |
| Investigation executed? | **YES** | Clicked "Investigate Incident"; backend synthesized analysis |
| InvestigationResult displayed? | **YES** | Signals, Hindsight context, hypotheses, steps, remediation rendered |
| Hindsight status honest? | **YES** | Correctly displays `HINDSIGHT OFFLINE` with explanation |

---

## 11. Captured Screenshots

Live headless browser screenshots were generated via automated script `frontend/scripts/capture_screenshots.js` and saved to `screenshots/`:

1. **Dashboard Overview (`screenshots/01_dashboard_overview.png`):**  
   Shows header status pills, incident list sidebar with filters and search, and initial incident view.
2. **Telemetry & Raw Logs (`screenshots/02_incident_telemetry.png`):**  
   Shows description, postmortem findings, extracted errors, and dark-mode terminal logs.
3. **Investigation Result — Signals & Memory (`screenshots/03_investigation_result.png`):**  
   Shows executive summary, deterministic signals grid, and honest Hindsight offline indicator.
4. **Investigation Result — Hypotheses & Remediation (`screenshots/04_investigation_hypotheses_remediation.png`):**  
   Shows ranked root-cause hypotheses with evidence, diagnostic steps, immediate mitigation, and long-term fixes.

---

## 12. Known Limitations

1. **Hindsight Server Connectivity:** The external Hindsight daemon (`http://localhost:8888`) is currently offline in the local developer environment (Docker Desktop engine stopped). The system gracefully degrades to current-incident deterministic telemetry and built-in heuristic reasoning, transparently disclosing this in the UI.
2. **In-Memory Storage:** Incidents remain in the in-memory repository; modifications and resolutions reset when the FastAPI backend process restarts.
3. **Synchronous Investigation Pipeline:** The investigation endpoint returns synchronously after complete synthesis; streaming progress steps are slated for future phases.

---

## 13. Recommended Phase 5

Now that the core agent reasoning pipeline (Phase 3) and full web dashboard (Phase 4) are operational, the recommended next architectural milestone is:

**PHASE 5 — REAL-TIME STREAMING & RUNBOOK PLAYBOOK EXECUTION**
1. **Server-Sent Events (SSE) or WebSockets:** Transition the investigation pipeline from a single blocking HTTP request to an SSE stream displaying live incremental progress stages (*Analyzing telemetry*, *Querying Hindsight*, *Evaluating hypotheses*).
2. **Interactive Diagnostic Workflows:** Allow engineers to check off or trigger non-destructive diagnostic verification queries directly from the investigation steps list.
3. **Persistent Postmortem Export:** Export the complete `InvestigationResult` as a Markdown postmortem report or incident ticket update.

# Hindsight-Powered Incident Response Agent

A production-oriented AI Incident Response Agent designed to assist engineers throughout the lifecycle of software incidents by leveraging **Hindsight** for long-term memory.

## Core Philosophy

Traditional incident response assistants suffer from session amnesia: once an incident is closed or a chat finishes, the investigation path, root-cause deductions, and postmortem lessons are lost. 

This project integrates the official **Hindsight** memory architecture to support three continuous memory cycles:
- **RETAIN**: Preserves confirmed root causes, mitigation steps, and incident postmortems into persistent memory banks.
- **RECALL**: Queries past incidents across semantic, graph, and temporal dimensions when a new outage occurs.
- **REFLECT**: Synthesizes complex historical hypotheses, discovering cross-incident patterns and recurring failure modes.

```
NEW INCIDENT
     ↓
Collect Evidence & Symptoms
     ↓
RECALL Historical Incidents (Hindsight)
     ↓
Analyze Current & Historical Context
     ↓
REFLECT & Synthesize Hypotheses (Hindsight)
     ↓
Investigate & Recommend Remediation
     ↓
Produce Incident Report
     ↓
RETAIN Outcome & Postmortem (Hindsight)
     ↓
Continuous Knowledge Growth for Future Outages
```

---

## Phase Status Summary

- [x] **Phase 1: Foundation & Hindsight Integration**
  - Project scaffolding, FastAPI application, Pydantic settings, logging.
  - Official `hindsight-client` setup with `client.py` and `memory.py` (RETAIN, RECALL, REFLECT).
  - Diagnostic verification CLI and HTTP health checks.
- [x] **Phase 2: Incident Schema, Repository & Hindsight Seed Data**
  - Pydantic incident domain models (`Incident`, `IncidentCreate`, `IncidentUpdate`, `IncidentResolve`, enums for `Severity` and `IncidentStatus`).
  - Decoupled `IncidentRepository` interface with thread-safe `InMemoryIncidentRepository`.
  - Full Incident REST API (`/api/v1/incidents` CRUD & `/resolve` lifecycle endpoint).
  - 10 realistic, diverse historical software incidents (`INC-2025-101` through `INC-2025-110`).
  - Hindsight seeding script with real RETAIN and RECALL verification tool (`backend/seed_hindsight.py`).
  - 40 automated tests covering schemas, repository lifecycle, API routes, seed data, and Hindsight operations.
- [ ] **Phase 3: Agent Core & Investigation Logic**
  - Incident summarization and log/error analysis.
  - Historical context retrieval & similarity analysis via Hindsight.
  - Automated hypothesis generation and remediation recommendation engine.
- [ ] **Phase 4: Web Dashboard (React + Vite)**
  - Interactive incident triage, investigation workspace, and timeline.
  - Visual memory recall inspection and postmortem resolution recorder.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14.3)
- Docker (optional, for local Hindsight container)

### 2. Installation
```bash
# Clone the repository
git clone <repo-url>
cd "Hindsight-Powered Incident Response Agent"

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```
Ensure `HINDSIGHT_BASE_URL` points to your instance:
- Local instance: `http://localhost:8888`
- Hindsight Cloud: `https://api.hindsight.vectorize.io` (set `HINDSIGHT_API_KEY`)

### 4. Verify Connection to Hindsight
Run the verification tool:
```bash
python backend/verify_hindsight.py
```

### 5. Seed Historical Incidents into Hindsight
```bash
python backend/seed_hindsight.py
```

### 6. Start the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for the interactive Swagger UI.

### 7. Run the Test Suite
```bash
pytest
```
All 40 unit and integration tests run in under 10 seconds.

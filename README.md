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

## Current Status: Phase 1 Completed

Phase 1 establishes the production-grade foundation:
- **FastAPI Backend Application**: Clean startup with async lifespan, structured logging, CORS support, and comprehensive health monitoring.
- **Official Hindsight Integration**: Dedicated `app/hindsight/` module with `HindsightClientManager` (lifecycle & resource management) and `HindsightMemoryService` implementing `RETAIN`, `RECALL`, and `REFLECT`.
- **Connectivity Verification**: Verification CLI script and HTTP endpoint (`/api/v1/hindsight/status`) that accurately probes server reachability without faking success.
- **Automated Test Suite**: 13 automated tests covering health endpoints, configuration loading, and Hindsight operations.
- **Frontend Placeholder**: Directory structure prepared for the React + Vite frontend in upcoming phases.

---

## Project Structure

```
├── .gitignore                      # Git ignore rules for Python, Node, & secrets
├── .env.example                    # Environment variable template
├── pytest.ini                      # Test runner configuration
├── requirements.txt                # Root requirements file
├── README.md                       # Main project documentation
├── backend/
│   ├── README.md                   # Backend documentation
│   ├── requirements.txt            # Backend dependencies
│   ├── .env.example                # Backend environment template
│   ├── verify_hindsight.py         # Verification CLI runner
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── core/
│   │   │   ├── config.py           # Configuration management (Pydantic Settings)
│   │   │   └── logging.py          # Structured logging
│   │   ├── hindsight/
│   │   │   ├── client.py           # Hindsight client manager & connection probe
│   │   │   ├── memory.py           # RETAIN, RECALL, REFLECT service layer
│   │   │   └── verify.py           # Verification script logic
│   │   └── api/
│   │       ├── router.py           # API routes aggregator
│   │       └── routes/
│   │           ├── health.py       # GET /health
│   │           └── hindsight.py    # GET /api/v1/hindsight/status
│   └── tests/
│       ├── conftest.py             # Test fixtures & config overrides
│       ├── test_config.py          # Config validation tests
│       ├── test_health.py          # Health check route tests
│       └── test_hindsight.py       # Client & memory service tests
└── frontend/
    └── README.md                   # Future UI architecture notes
```

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

### 5. Start the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for the OpenAPI interactive Swagger UI.

### 6. Run the Test Suite
```bash
pytest
```

---

## Phase Roadmap

- [x] **Phase 1: Foundation & Hindsight Integration**
  - Project scaffolding, FastAPI application, Pydantic settings, logging.
  - Official `hindsight-client` setup with `client.py` and `memory.py` (RETAIN, RECALL, REFLECT).
  - Diagnostic verification CLI and HTTP health checks.
  - Test suite with 13 automated tests.
- [ ] **Phase 2: Incident Schema & Simulation Data**
  - Structured Incident models (ID, Title, Service, Severity, Logs, Errors, Status).
  - Seed dataset of realistic incident scenarios.
  - Storage/repository interface.
- [ ] **Phase 3: Agent Core & Investigation Logic**
  - Incident summarization and log/error analysis.
  - Retrieval and synthesis of historical incidents using Hindsight.
  - Hypothesis generation and remediation recommendation engine.
- [ ] **Phase 4: Web Dashboard (React + Vite)**
  - Interactive incident triage, timeline, and agent investigation workspace.
  - Visual memory recall inspection and postmortem resolution recorder.

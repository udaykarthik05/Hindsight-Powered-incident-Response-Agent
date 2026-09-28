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
Deterministic Signal Extraction (app/agent/analysis.py)
     ↓
RECALL Historical Incidents (Hindsight Memory)
     ↓
REFLECT & Synthesize Comparative Reasoning (Hindsight Memory)
     ↓
LLM Synthesis & Hypothesis Generation (app/agent/llm.py)
     ↓
Structured Investigation Result (Ranked Hypotheses + Non-destructive Steps + Remediation)
     ↓
Incident Resolution & Postmortem
     ↓
RETAIN Outcome & Learnings (Hindsight Memory)
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
- [x] **Phase 3: Agent Core & Investigation Logic**
  - Deterministic signal analysis layer extracting errors, subsystems, deployment correlations, and candidate categories.
  - Hindsight RECALL & REFLECT integration constructing dynamic evidence-based queries.
  - LLM synthesis layer supporting OpenAI-compatible providers with a built-in heuristic reasoning engine.
  - Structured output (`InvestigationResult`, `Hypothesis`, `InvestigationStep`, `RemediationPlan`).
  - `POST /api/v1/incidents/{incident_id}/investigate` endpoint.
  - Offline resilience: gracefully degrades without fabricating memories when Hindsight is unreachable.
  - 51 automated unit and integration tests passing.
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
Key configuration parameters:
- `HINDSIGHT_BASE_URL`: URL of your Hindsight instance (`http://localhost:8888` for local Docker or `https://api.hindsight.vectorize.io` for cloud).
- `HINDSIGHT_API_KEY`: API key if using cloud or secured instance.
- `HINDSIGHT_BANK_ID`: Target memory bank for incident knowledge.
- `LLM_PROVIDER`: `"openai"`, `"gemini"`, `"groq"`, `"ollama"`, or `"heuristic"`.
- `LLM_API_KEY`: API key for LLM provider (leave blank to run the built-in heuristic reasoning engine).

### 4. Verify Connection to Hindsight
```bash
python backend/verify_hindsight.py
```

### 5. Seed Historical Incidents into Hindsight
```bash
python backend/seed_hindsight.py
```

### 6. Run Live Agent Investigation CLI Demo
```bash
python backend/verify_investigation.py
```

### 7. Start the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for the OpenAPI interactive Swagger UI.

### 8. Run the Test Suite
```bash
pytest
```
All 51 unit and integration tests run in ~12 seconds.

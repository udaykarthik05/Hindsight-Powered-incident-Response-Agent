# Incident Response Agent - Backend

FastAPI backend service integrating official **Hindsight** memory for AI-assisted incident response.

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, lifespan, CORS, and root routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings loaded from .env
│   │   └── logging.py           # Structured logging configuration
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── incident.py          # Incident, IncidentCreate, IncidentUpdate, IncidentResolve, Enums
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── incident_repository.py # In-memory thread-safe repository abstraction
│   ├── data/
│   │   ├── __init__.py
│   │   └── seed_incidents.py    # Curated dataset of 10 realistic historical incidents
│   ├── hindsight/
│   │   ├── __init__.py
│   │   ├── client.py            # Official Hindsight SDK client manager & health check
│   │   ├── memory.py            # Domain operations: RETAIN, RECALL, REFLECT
│   │   ├── seed.py              # Live RETAIN seeder & RECALL verifier
│   │   └── verify.py            # Standalone CLI connectivity verification tool
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── models.py            # InvestigationResult, Hypothesis, ObservedSignals, RemediationPlan
│   │   ├── analysis.py          # Deterministic signal extraction & recall query builder
│   │   ├── prompts.py           # System & user prompts for LLM synthesis
│   │   ├── llm.py               # OpenAI-compatible LLM client + HeuristicReasoningEngine
│   │   ├── incident_agent.py    # IncidentResponseAgent orchestrator
│   │   └── verify_investigation.py # CLI demonstration of live agent investigation
│   └── api/
│       ├── __init__.py
│       ├── router.py            # Root API router
│       └── routes/
│           ├── __init__.py
│           ├── health.py        # GET /health
│           ├── incidents.py     # Incident CRUD, resolve, and investigate endpoints
│           └── hindsight.py     # GET /api/v1/hindsight/status & memory endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures and environment setup
│   ├── test_config.py           # Configuration loading & validation tests
│   ├── test_health.py           # Health endpoint tests
│   ├── test_hindsight.py        # Hindsight client manager & memory service tests
│   ├── test_hindsight_seed_unit.py # Unit tests for memory seeding & offline handling
│   ├── test_incident_schemas.py # Incident schema validation tests
│   ├── test_incident_repository.py # Repository CRUD & lifecycle tests
│   ├── test_incident_api.py     # Incident API endpoint integration tests
│   ├── test_seed_data.py        # Seed dataset completeness & formatting validation
│   ├── test_agent_analysis.py   # Deterministic signal extraction tests
│   ├── test_agent_core.py       # Agent core orchestrator & offline tests
│   ├── test_agent_api.py        # POST /api/v1/incidents/{id}/investigate tests
│   └── test_demo_scenario.py    # Phase 3 payment API demo scenario verification
├── verify_hindsight.py          # Script runner for connection verification
├── seed_hindsight.py            # Script runner for Hindsight seeding & verification
├── verify_investigation.py      # Script runner for agent investigation demo
├── requirements.txt             # Pinned backend dependencies
├── .env.example                 # Environment configuration template
└── README.md
```

## Quick Start

### 1. Set Up Environment
```bash
# From workspace root
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configuration parameters:
- `HINDSIGHT_BASE_URL`: URL of your Hindsight instance (`http://localhost:8888` for local Docker or `https://api.hindsight.vectorize.io` for cloud).
- `HINDSIGHT_API_KEY`: API key if using cloud or secured instance.
- `HINDSIGHT_BANK_ID`: Target memory bank for incident knowledge.
- `LLM_PROVIDER`: `"openai"`, `"gemini"`, `"groq"`, `"ollama"`, or `"heuristic"`.
- `LLM_API_KEY`: API key for LLM provider (leave blank to run the built-in heuristic reasoning engine).

### 3. Verify Hindsight Connectivity
```bash
python backend/verify_hindsight.py
```

### 4. Seed Hindsight with Historical Incidents
```bash
python backend/seed_hindsight.py
```

### 5. Run Live Agent Investigation CLI Demo
```bash
python backend/verify_investigation.py
```
Executes the full pipeline: deterministic analysis -> Hindsight query -> reasoning engine -> structured output.

### 6. Run the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs are available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

#### Available Endpoints:
- `GET /health`: Basic health check.
- `POST /api/v1/incidents`: Register a new incident.
- `GET /api/v1/incidents`: List incidents (filters: `?status=`, `?severity=`, `?service=`).
- `GET /api/v1/incidents/{incident_id}`: Retrieve incident details.
- `PATCH /api/v1/incidents/{incident_id}`: Partially update incident.
- `POST /api/v1/incidents/{incident_id}/resolve`: Resolve incident with root cause & mitigation.
- `POST /api/v1/incidents/{incident_id}/investigate`: Run AI investigation pipeline on the incident.
- `GET /api/v1/hindsight/status`: Check Hindsight server connectivity.

### 7. Run Tests
```bash
pytest backend/tests -v
```
All 51 unit and integration tests run in ~12 seconds.

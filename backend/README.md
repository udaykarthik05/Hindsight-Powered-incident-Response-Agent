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
│   └── api/
│       ├── __init__.py
│       ├── router.py            # Root API router
│       └── routes/
│           ├── __init__.py
│           ├── health.py        # GET /health
│           ├── incidents.py     # Incident CRUD & resolution endpoints
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
│   └── test_seed_data.py        # Seed dataset completeness & formatting validation
├── verify_hindsight.py          # Script runner for connection verification
├── seed_hindsight.py            # Script runner for Hindsight seeding & verification
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

### 3. Verify Hindsight Connectivity
```bash
python backend/verify_hindsight.py
```
This tests network connectivity to Hindsight and reports server version and status without faking results.

### 4. Seed Hindsight with Historical Incidents
```bash
python backend/seed_hindsight.py
```
Checks reachability, ingests 10 rich historical postmortems via `RETAIN`, and verifies retention with a real `RECALL` query.

### 5. Run the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs are available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

#### Available Endpoints:
- `GET /health`: Basic health check.
- `POST /api/v1/incidents`: Register a new incident.
- `GET /api/v1/incidents`: List incidents (filters: `status`, `severity`, `service`).
- `GET /api/v1/incidents/{incident_id}`: Retrieve incident details.
- `PATCH /api/v1/incidents/{incident_id}`: Partially update incident.
- `POST /api/v1/incidents/{incident_id}/resolve`: Resolve incident with root cause & mitigation.
- `GET /api/v1/hindsight/status`: Check Hindsight server connectivity.

### 6. Run Tests
```bash
pytest backend/tests -v
```
All 40 unit and integration tests run in under 10 seconds.

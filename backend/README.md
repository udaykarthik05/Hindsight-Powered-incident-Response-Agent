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
│   ├── hindsight/
│   │   ├── __init__.py
│   │   ├── client.py            # Official Hindsight SDK client manager & health check
│   │   ├── memory.py            # Domain operations: RETAIN, RECALL, REFLECT
│   │   └── verify.py            # Standalone CLI connectivity verification tool
│   └── api/
│       ├── __init__.py
│       ├── router.py            # Root API router
│       └── routes/
│           ├── __init__.py
│           ├── health.py        # GET /health
│           └── hindsight.py     # GET /api/v1/hindsight/status & memory endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures and environment setup
│   ├── test_config.py           # Configuration loading & validation tests
│   ├── test_health.py           # Health endpoint tests
│   └── test_hindsight.py        # Hindsight client manager & memory service tests
├── verify_hindsight.py          # Script runner for connection verification
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
Run the diagnostic script:
```bash
python backend/verify_hindsight.py
```
This tests network connectivity to Hindsight and reports server version and status without faking results.

### 4. Run the Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`
- Hindsight status: `http://127.0.0.1:8000/api/v1/hindsight/status`

### 5. Run Tests
```bash
pytest backend/tests -v
```

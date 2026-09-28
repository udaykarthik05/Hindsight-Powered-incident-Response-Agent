from datetime import datetime, timezone
import pytest

from app.agent.analysis import DeterministicAnalyzer
from app.schemas.incident import Incident, IncidentStatus, Severity


def test_analyze_database_incident() -> None:
    """Test deterministic analysis extracts DB and connection pool indicators."""
    incident = Incident(
        incident_id="INC-TEST-DB",
        title="Postgres Connection Limit Reached in Order Service",
        description="Checkout transactions hanging. Database error log indicates max connections exhausted.",
        severity=Severity.CRITICAL,
        affected_service="order-service",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "ERROR: psycopg2.OperationalError: remaining connection slots are reserved for non-replication superuser connections",
            "WARN: HikariPool-1 - Connection is not available, request timed out after 30000ms.",
        ],
        error_messages=["psycopg2.OperationalError: remaining connection slots are reserved"],
        status=IncidentStatus.OPEN,
    )

    signals, recall_query = DeterministicAnalyzer.analyze(incident)

    assert "database" in signals.infrastructure_components
    assert "connection pool" in signals.infrastructure_components
    assert "Database Connection Pool Exhaustion" in signals.suspected_categories
    assert "order-service" in recall_query
    assert "database" in recall_query.lower()


def test_analyze_auth_incident() -> None:
    """Test deterministic analysis extracts JWT and auth indicators."""
    incident = Incident(
        incident_id="INC-TEST-AUTH",
        title="Token Verification Failures across API Gateway",
        description="Users receiving 401 Unauthorized en masse. JWKS token validation failing.",
        severity=Severity.HIGH,
        affected_service="api-gateway",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "ERROR: jwt.exceptions.ExpiredSignatureError: Signature has expired for keyId 'auth-key-prod'",
            "WARN: KeyVerificationError: Unable to verify token signature",
        ],
        error_messages=["ExpiredSignatureError: Signature has expired"],
        status=IncidentStatus.OPEN,
    )

    signals, recall_query = DeterministicAnalyzer.analyze(incident)

    assert "auth security" in signals.infrastructure_components
    assert "Authentication / Key Expiry Failure" in signals.suspected_categories
    assert any("jwt" in e.lower() or "expired" in e.lower() for e in signals.error_types)
    assert "api-gateway" in recall_query


def test_analyze_network_incident() -> None:
    """Test deterministic analysis extracts DNS and network resolution errors."""
    incident = Incident(
        incident_id="INC-TEST-NET",
        title="Internal Microservice DNS Resolution Timeout",
        description="Inter-service gRPC calls failing with name resolution timeouts.",
        severity=Severity.HIGH,
        affected_service="inventory-service",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "ERROR: gaierror: [Errno -2] Name or service not known for order-service.svc.cluster.local",
            "WARN: CoreDNS: 53 udp: i/o timeout resolving inventory-service",
        ],
        error_messages=["gaierror: Name or service not known"],
        status=IncidentStatus.OPEN,
    )

    signals, recall_query = DeterministicAnalyzer.analyze(incident)

    assert "dns network" in signals.infrastructure_components
    assert "DNS / Service Discovery Failure" in signals.suspected_categories
    assert "inventory-service" in recall_query


def test_analyze_deployment_regression_incident() -> None:
    """Test deterministic analysis detects deployment correlation and migration locks."""
    incident = Incident(
        incident_id="INC-TEST-DEPLOY",
        title="Post-Release User Table Lock Degradation",
        description="Errors spiked immediately after recent release v2.5.0 and Alembic database migration rollout.",
        severity=Severity.CRITICAL,
        affected_service="user-service",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "ERROR: PostgreSQL query waiting for AccessExclusiveLock on relation 'users'",
            "ERROR: django.db.utils.OperationalError: lock wait timeout exceeded",
        ],
        error_messages=["Lock wait timeout exceeded"],
        status=IncidentStatus.OPEN,
    )

    signals, recall_query = DeterministicAnalyzer.analyze(incident)

    assert signals.deployment_correlated is True
    assert any("Deployment Regression" in cat for cat in signals.suspected_categories)
    assert "database" in signals.infrastructure_components

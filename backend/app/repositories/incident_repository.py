from abc import ABC, abstractmethod
from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)

logger = get_logger("repository.incident")


class IncidentRepository(ABC):
    """Abstract interface for incident persistence and retrieval."""

    @abstractmethod
    def create(self, incident_in: IncidentCreate) -> Incident:
        """Create and persist a new incident."""
        pass

    @abstractmethod
    def get(self, incident_id: str) -> Optional[Incident]:
        """Retrieve an incident by unique identifier."""
        pass

    @abstractmethod
    def list(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[Severity] = None,
        service: Optional[str] = None,
    ) -> List[Incident]:
        """List incidents with optional filtering."""
        pass

    @abstractmethod
    def update(self, incident_id: str, update_in: IncidentUpdate) -> Optional[Incident]:
        """Update fields of an existing incident."""
        pass

    @abstractmethod
    def resolve(self, incident_id: str, resolve_in: IncidentResolve) -> Optional[Incident]:
        """Mark an incident as resolved with root cause and mitigation."""
        pass

    @abstractmethod
    def delete(self, incident_id: str) -> bool:
        """Delete an incident by ID."""
        pass

    @abstractmethod
    def seed(self, incidents: List[Incident]) -> int:
        """Seed the repository with pre-defined incidents."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored incidents."""
        pass


class InMemoryIncidentRepository(IncidentRepository):
    """Thread-safe in-memory implementation of IncidentRepository."""

    def __init__(self) -> None:
        self._storage: Dict[str, Incident] = {}
        self._lock = threading.RLock()

    def create(self, incident_in: IncidentCreate) -> Incident:
        with self._lock:
            incident = Incident.create_from_input(incident_in)
            self._storage[incident.incident_id] = incident
            logger.info("Created incident %s: '%s'", incident.incident_id, incident.title)
            return incident

    def get(self, incident_id: str) -> Optional[Incident]:
        with self._lock:
            return self._storage.get(incident_id)

    def list(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[Severity] = None,
        service: Optional[str] = None,
    ) -> List[Incident]:
        with self._lock:
            results = list(self._storage.values())

            if status is not None:
                results = [inc for inc in results if inc.status == status]
            if severity is not None:
                results = [inc for inc in results if inc.severity == severity]
            if service is not None:
                results = [
                    inc for inc in results
                    if inc.affected_service.lower() == service.lower()
                ]

            # Return sorted by timestamp descending (newest first)
            results.sort(key=lambda inc: inc.timestamp, reverse=True)
            return results

    def update(self, incident_id: str, update_in: IncidentUpdate) -> Optional[Incident]:
        with self._lock:
            existing = self._storage.get(incident_id)
            if not existing:
                return None

            update_data = update_in.model_dump(exclude_unset=True)

            # Preserve immutable / managed attributes
            current_dict = existing.model_dump()
            current_dict.update(update_data)

            # Update resolved_at if status changed to resolved
            if update_in.status == IncidentStatus.RESOLVED and not current_dict.get("resolved_at"):
                current_dict["resolved_at"] = datetime.now(timezone.utc)
            elif update_in.status in (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING):
                current_dict["resolved_at"] = None

            updated_incident = Incident(**current_dict)
            self._storage[incident_id] = updated_incident
            logger.info("Updated incident %s", incident_id)
            return updated_incident

    def resolve(self, incident_id: str, resolve_in: IncidentResolve) -> Optional[Incident]:
        with self._lock:
            existing = self._storage.get(incident_id)
            if not existing:
                return None

            now = resolve_in.resolved_at or datetime.now(timezone.utc)
            resolved_dict = existing.model_dump()
            resolved_dict["status"] = IncidentStatus.RESOLVED
            resolved_dict["root_cause"] = resolve_in.root_cause
            resolved_dict["mitigation"] = resolve_in.mitigation
            resolved_dict["resolved_at"] = now

            resolved_incident = Incident(**resolved_dict)
            self._storage[incident_id] = resolved_incident
            logger.info("Resolved incident %s with root cause", incident_id)
            return resolved_incident

    def delete(self, incident_id: str) -> bool:
        with self._lock:
            if incident_id in self._storage:
                del self._storage[incident_id]
                logger.info("Deleted incident %s", incident_id)
                return True
            return False

    def seed(self, incidents: List[Incident]) -> int:
        with self._lock:
            count = 0
            for inc in incidents:
                self._storage[inc.incident_id] = inc
                count += 1
            logger.info("Seeded %d incidents into in-memory repository", count)
            return count

    def count(self) -> int:
        with self._lock:
            return len(self._storage)


# Global singleton repository instance
_incident_repository: Optional[IncidentRepository] = None


def get_incident_repository() -> IncidentRepository:
    """Dependency provider returning singleton IncidentRepository."""
    global _incident_repository
    if _incident_repository is None:
        _incident_repository = InMemoryIncidentRepository()
    return _incident_repository

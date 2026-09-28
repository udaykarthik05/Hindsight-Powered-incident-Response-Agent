from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.incident_repository import (
    IncidentRepository,
    get_incident_repository,
)
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post(
    "",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
)
def create_incident(
    payload: IncidentCreate,
    repo: IncidentRepository = Depends(get_incident_repository),
) -> Incident:
    """
    Register and persist a new software incident.
    
    Generates an incident identifier (e.g. `INC-YYYYMMDD-XXXX`) if not explicitly specified.
    """
    return repo.create(payload)


@router.get(
    "",
    response_model=List[Incident],
    summary="List all incidents with optional filtering",
)
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status", description="Filter by lifecycle status"),
    severity: Optional[Severity] = Query(None, description="Filter by severity level"),
    service: Optional[str] = Query(None, description="Filter by affected service name"),
    repo: IncidentRepository = Depends(get_incident_repository),
) -> List[Incident]:
    """
    Retrieve incidents sorted chronologically (most recent first).
    
    Supports query filtering across status, severity, and affected service.
    """
    return repo.list(status=status_filter, severity=severity, service=service)


@router.get(
    "/{incident_id}",
    response_model=Incident,
    summary="Get incident details by ID",
)
def get_incident(
    incident_id: str,
    repo: IncidentRepository = Depends(get_incident_repository),
) -> Incident:
    """
    Retrieve detailed records for a specific incident by its unique ID.
    """
    incident = repo.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return incident


@router.patch(
    "/{incident_id}",
    response_model=Incident,
    summary="Update an existing incident",
)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    repo: IncidentRepository = Depends(get_incident_repository),
) -> Incident:
    """
    Perform partial updates on an existing incident (e.g., updating severity, adding logs, or modifying description).
    """
    updated = repo.update(incident_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return updated


@router.post(
    "/{incident_id}/resolve",
    response_model=Incident,
    summary="Mark an incident as resolved",
)
def resolve_incident(
    incident_id: str,
    payload: IncidentResolve,
    repo: IncidentRepository = Depends(get_incident_repository),
) -> Incident:
    """
    Transition an incident to 'resolved' status, attaching mandatory root cause analysis and mitigation details.
    """
    resolved = repo.resolve(incident_id, payload)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return resolved

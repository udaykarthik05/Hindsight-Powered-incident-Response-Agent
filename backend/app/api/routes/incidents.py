from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.agent.incident_agent import IncidentResponseAgent, get_incident_agent
from app.agent.models import InvestigationResult
from app.hindsight.lifecycle import (
    HindsightMemoryLifecycle,
    get_memory_lifecycle,
)
from app.repositories.incident_repository import (
    IncidentRepository,
    get_incident_repository,
)
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentResolveResponse,
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
    response_model=IncidentResolveResponse,
    summary="Mark an incident as resolved and retain memory into Hindsight",
)
async def resolve_incident(
    incident_id: str,
    payload: IncidentResolve,
    repo: IncidentRepository = Depends(get_incident_repository),
    lifecycle: HindsightMemoryLifecycle = Depends(get_memory_lifecycle),
) -> IncidentResolveResponse:
    """
    Transition an incident to 'resolved' status, attaching mandatory root cause analysis and mitigation details,
    and retain the postmortem record into Hindsight organizational memory.
    
    If Hindsight is offline or unreachable, resolution succeeds and remains recorded; memory retention
    failure is reported gracefully in the response envelope without corrupting incident state.
    """
    resolved = repo.resolve(incident_id, payload)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )

    # Ingest postmortem into Hindsight organizational memory (graceful on error)
    retention_result = await lifecycle.retain_resolved_incident(resolved)

    # Update repository with the resulting memory status
    updated_resolved = repo.update(
        incident_id,
        IncidentUpdate(memory_status=retention_result.status.value),
    ) or resolved

    res_dict = updated_resolved.model_dump()
    res_dict["memory_status"] = retention_result.status.value
    res_dict["memory_message"] = retention_result.message
    return IncidentResolveResponse(**res_dict)


@router.post(
    "/{incident_id}/investigate",
    response_model=InvestigationResult,
    summary="Run AI incident investigation pipeline",
)
async def investigate_incident(
    incident_id: str,
    repo: IncidentRepository = Depends(get_incident_repository),
    agent: IncidentResponseAgent = Depends(get_incident_agent),
) -> InvestigationResult:
    """
    Execute the AI Incident Response Agent reasoning pipeline for the specified incident:
    1. Loads current incident telemetry and metadata
    2. Runs deterministic evidence analysis
    3. Queries Hindsight RECALL & REFLECT for historical context
    4. Generates ranked hypotheses, non-destructive investigation steps, and remediations.
    """
    incident = repo.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return await agent.investigate(incident)

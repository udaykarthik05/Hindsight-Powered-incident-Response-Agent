from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from app.hindsight.client import (
    HindsightClientManager,
    HindsightConnectionStatus,
    get_hindsight_manager,
)
from app.hindsight.memory import (
    HindsightMemoryService,
    HindsightOperationError,
    MemoryRecallInput,
    MemoryReflectInput,
    MemoryRetainInput,
    get_memory_service,
)

router = APIRouter(prefix="/hindsight", tags=["Hindsight Memory"])


@router.get("/status", response_model=HindsightConnectionStatus)
async def get_hindsight_status(
    manager: HindsightClientManager = Depends(get_hindsight_manager),
) -> HindsightConnectionStatus:
    """
    Check real-time connectivity to the configured Hindsight server.
    
    Returns connection state, active bank ID, server version (if reachable),
    or detailed troubleshooting information without faking connectivity.
    """
    return await manager.check_connection()


@router.post("/retain", response_model=Dict[str, Any])
async def retain_memory(
    body: MemoryRetainInput,
    service: HindsightMemoryService = Depends(get_memory_service),
) -> Dict[str, Any]:
    """
    Store an incident insight, resolution, or postmortem into Hindsight memory.
    """
    try:
        response = await service.retain(body)
        return response.model_dump()
    except HindsightOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )


@router.post("/recall", response_model=Dict[str, Any])
async def recall_memory(
    body: MemoryRecallInput,
    service: HindsightMemoryService = Depends(get_memory_service),
) -> Dict[str, Any]:
    """
    Recall relevant historical incident memories matching query symptoms or service names.
    """
    try:
        response = await service.recall(body)
        return response.model_dump()
    except HindsightOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )


@router.post("/reflect", response_model=Dict[str, Any])
async def reflect_memory(
    body: MemoryReflectInput,
    service: HindsightMemoryService = Depends(get_memory_service),
) -> Dict[str, Any]:
    """
    Synthesize high-level reasoning across historical incident memories.
    """
    try:
        response = await service.reflect(body)
        return response.model_dump()
    except HindsightOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(err),
        )

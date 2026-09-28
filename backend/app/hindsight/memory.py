from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from hindsight_client import (
    RecallResponse,
    ReflectResponse,
    RetainResponse,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.hindsight.client import HindsightClientManager, get_hindsight_manager

logger = get_logger("hindsight.memory")


# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------

class HindsightError(Exception):
    """Base exception for Hindsight memory operations."""
    pass


class HindsightConnectionError(HindsightError):
    """Raised when the Hindsight service is unreachable."""
    pass


class HindsightOperationError(HindsightError):
    """Raised when an operation (retain, recall, reflect) fails."""
    pass


# ------------------------------------------------------------------------------
# Request & Response Data Transfer Objects (DTOs)
# ------------------------------------------------------------------------------

class MemoryRetainInput(BaseModel):
    """Parameters for retaining incident knowledge in Hindsight."""
    content: Union[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Text content or message list describing the incident or postmortem",
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional contextual scope, e.g., 'Incident INC-102 postmortem'",
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Structured key-value pairs (e.g., service, severity, incident_id)",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Classification tags (e.g., ['database', 'timeout', 'p1'])",
    )
    bank_id: Optional[str] = Field(
        default=None,
        description="Target memory bank (defaults to configured application bank)",
    )


class MemoryRecallInput(BaseModel):
    """Parameters for recalling historical incident knowledge from Hindsight."""
    query: str = Field(
        ...,
        description="Natural language query or incident symptoms to match against history",
    )
    types: Optional[List[str]] = Field(
        default=None,
        description="Filter by memory types (e.g., 'world', 'experience', 'observation')",
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum token budget for retrieved context",
    )
    budget: str = Field(
        default="mid",
        description="Recall retrieval budget / depth: 'low', 'mid', 'high'",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter results by matching tags",
    )
    bank_id: Optional[str] = Field(
        default=None,
        description="Target memory bank (defaults to configured application bank)",
    )


class MemoryReflectInput(BaseModel):
    """Parameters for reflecting upon historical memories to synthesize insights."""
    query: str = Field(
        ...,
        description="Complex reasoning query, e.g., 'Have we seen similar payment gateway timeouts before?'",
    )
    context: Optional[str] = Field(
        default=None,
        description="Current incident details to contrast against historical knowledge",
    )
    budget: str = Field(
        default="low",
        description="Reflect compute budget: 'low', 'mid', 'high'",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter memory units considered in reflection",
    )
    bank_id: Optional[str] = Field(
        default=None,
        description="Target memory bank (defaults to configured application bank)",
    )


# ------------------------------------------------------------------------------
# Hindsight Memory Service
# ------------------------------------------------------------------------------

class HindsightMemoryService:
    """
    Core service encapsulating Hindsight memory lifecycle operations:
    - RETAIN: Persist incident resolutions, postmortems, and learnings.
    - RECALL: Retrieve relevant historical incidents and evidence.
    - REFLECT: Synthesize complex historical hypotheses and pattern deductions.
    
    Strictly interfaces with official Hindsight SDK without fallbacks to fake stores.
    """

    def __init__(
        self,
        manager: Optional[HindsightClientManager] = None,
        settings: Optional[Settings] = None,
    ):
        self.manager = manager or get_hindsight_manager()
        self.settings = settings or get_settings()

    def _resolve_bank_id(self, bank_id: Optional[str]) -> str:
        """Resolve target memory bank ID, defaulting to application configuration."""
        return bank_id or self.settings.hindsight_bank_id

    async def retain(self, retain_input: MemoryRetainInput) -> RetainResponse:
        """
        Ingest incident details, root cause analyses, or remediation steps into Hindsight.
        """
        bank_id = self._resolve_bank_id(retain_input.bank_id)
        client = self.manager.get_client()

        logger.info(
            "Retaining incident memory in bank '%s' (tags: %s)",
            bank_id,
            retain_input.tags,
        )

        try:
            response: RetainResponse = await client.aretain(
                bank_id=bank_id,
                content=retain_input.content,
                context=retain_input.context,
                metadata=retain_input.metadata,
                tags=retain_input.tags,
            )
            logger.info("Successfully retained memory units (bank: %s)", bank_id)
            return response
        except Exception as err:
            logger.error("Hindsight RETAIN failed: %s", err, exc_info=True)
            raise HindsightOperationError(f"Failed to retain incident memory: {err}") from err

    async def recall(self, recall_input: MemoryRecallInput) -> RecallResponse:
        """
        Recall relevant historical incidents matching query symptoms or service names.
        """
        bank_id = self._resolve_bank_id(recall_input.bank_id)
        client = self.manager.get_client()

        logger.info(
            "Recalling incident memory from bank '%s' for query: '%s'",
            bank_id,
            recall_input.query,
        )

        try:
            response: RecallResponse = await client.arecall(
                bank_id=bank_id,
                query=recall_input.query,
                types=recall_input.types,
                max_tokens=recall_input.max_tokens,
                budget=recall_input.budget,
                tags=recall_input.tags,
            )
            count = len(response.results) if response.results else 0
            logger.info("Recalled %d relevant historical memory items", count)
            return response
        except Exception as err:
            logger.warning("Hindsight RECALL failed: %s", err)
            raise HindsightOperationError(f"Failed to recall incident memories: {err}") from err

    async def reflect(self, reflect_input: MemoryReflectInput) -> ReflectResponse:
        """
        Perform reflective reasoning over historical incidents to synthesize hypotheses.
        """
        bank_id = self._resolve_bank_id(reflect_input.bank_id)
        client = self.manager.get_client()

        logger.info(
            "Reflecting upon historical memory in bank '%s' for query: '%s'",
            bank_id,
            reflect_input.query,
        )

        try:
            response: ReflectResponse = await client.areflect(
                bank_id=bank_id,
                query=reflect_input.query,
                budget=reflect_input.budget,
                context=reflect_input.context,
                tags=reflect_input.tags,
            )
            logger.info("Hindsight reflection synthesized successfully.")
            return response
        except Exception as err:
            logger.warning("Hindsight REFLECT failed: %s", err)
            raise HindsightOperationError(f"Failed to reflect upon incident memory: {err}") from err


# Service factory function
def get_memory_service() -> HindsightMemoryService:
    """Dependency provider for HindsightMemoryService."""
    return HindsightMemoryService()

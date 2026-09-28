"""Hindsight integration module providing client lifecycle and memory operations."""

from app.hindsight.client import (
    HindsightClientManager,
    HindsightConnectionStatus,
    get_hindsight_manager,
)
from app.hindsight.memory import (
    HindsightError,
    HindsightConnectionError,
    HindsightOperationError,
    HindsightMemoryService,
    MemoryRetainInput,
    MemoryRecallInput,
    MemoryReflectInput,
    get_memory_service,
)

__all__ = [
    "HindsightClientManager",
    "HindsightConnectionStatus",
    "get_hindsight_manager",
    "HindsightError",
    "HindsightConnectionError",
    "HindsightOperationError",
    "HindsightMemoryService",
    "MemoryRetainInput",
    "MemoryRecallInput",
    "MemoryReflectInput",
    "get_memory_service",
]

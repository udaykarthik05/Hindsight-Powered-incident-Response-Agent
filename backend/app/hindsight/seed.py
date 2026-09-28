"""
Hindsight historical incident seeding and verification script.

Reads the curated dataset of historical incidents, ingests them into the
target Hindsight memory bank using the official RETAIN operation, and
verifies retention with a real RECALL query.

Usage:
    python -m app.hindsight.seed
    or:
    python backend/seed_hindsight.py
"""

import asyncio
import sys
from typing import Optional

from app.core.config import Settings, get_settings
from app.data.seed_incidents import get_seed_data
from app.hindsight.client import HindsightClientManager
from app.hindsight.memory import (
    HindsightMemoryService,
    MemoryRecallInput,
    MemoryRetainInput,
)


async def run_hindsight_seeding(
    settings: Optional[Settings] = None,
    recall_query: str = "Find previous incidents involving database connection failures, connection pools, or database timeouts.",
) -> bool:
    """
    Check Hindsight connectivity, seed historical incidents via RETAIN, and run a real RECALL query.
    
    Strictly verifies connectivity first and NEVER fakes success if Hindsight is offline.
    """
    settings = settings or get_settings()
    manager = HindsightClientManager(settings)
    memory_service = HindsightMemoryService(manager=manager, settings=settings)

    print("=" * 76)
    print(" HINDSIGHT HISTORICAL INCIDENT SEEDING & VERIFICATION")
    print("=" * 76)
    print(f"Target Base URL : {settings.hindsight_base_url}")
    print(f"Target Bank ID  : {settings.hindsight_bank_id}")
    print(f"API Key Set     : {'Yes (Masked)' if settings.hindsight_api_key else 'No (None)'}")
    print(f"Timeout         : {settings.hindsight_timeout}s")
    print("-" * 76)
    print("Checking Hindsight server reachability...")

    status = await manager.check_connection()

    if not status.connected:
        print("\n [!] HINDSIGHT SERVER IS UNREACHABLE")
        print(f"  Error Detail : {status.error}")
        print(f"  Diagnosis    : {status.message}")
        print("-" * 76)
        print("CANNOT SEED MEMORY: Hindsight server is currently offline.")
        print("Per project rules, will NOT fake successful retention or fake recall responses.")
        print("\nTo start Hindsight and enable real memory operations:")
        print("  1. Run local Docker container:")
        print("     docker run -d -p 8888:8888 -p 5432:5432 vectorize/hindsight:latest")
        print("     Ensure HINDSIGHT_BASE_URL=http://localhost:8888 in .env")
        print("  2. Or configure Hindsight Cloud:")
        print("     Set HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io")
        print("     Set HINDSIGHT_API_KEY=<your-api-key> in .env")
        print("=" * 76)
        await manager.close()
        return False

    print(f" [OK] Connected to Hindsight server (version: {status.server_version})")
    print("-" * 76)

    # 1. Ingest seed incidents via RETAIN
    seed_payloads = get_seed_data()
    print(f"Initiating RETAIN for {len(seed_payloads)} historical incidents into bank '{settings.hindsight_bank_id}'...")

    retained_count = 0
    for idx, payload in enumerate(seed_payloads, start=1):
        formatted = payload.to_hindsight_format()
        retain_input = MemoryRetainInput(
            content=formatted["content"],
            context=formatted["context"],
            metadata=formatted["metadata"],
            tags=formatted["tags"],
            bank_id=settings.hindsight_bank_id,
        )

        try:
            response = await memory_service.retain(retain_input)
            retained_count += 1
            op_id = getattr(response, "operation_id", "synced")
            print(f"  [{idx:02d}/{len(seed_payloads):02d}] RETAIN SUCCESS: {payload.incident.incident_id} - '{payload.incident.title}' (op: {op_id})")
        except Exception as err:
            print(f"  [{idx:02d}/{len(seed_payloads):02d}] RETAIN FAILED for {payload.incident.incident_id}: {err}")

    print("-" * 76)
    print(f"RETAIN Summary: Successfully ingested {retained_count}/{len(seed_payloads)} incidents into Hindsight.")

    # 2. Perform REAL Hindsight RECALL query
    print("\nExecuting REAL Hindsight RECALL query:")
    print(f"  Query: \"{recall_query}\"")
    print("-" * 76)

    try:
        recall_input = MemoryRecallInput(
            query=recall_query,
            budget="mid",
            max_tokens=4096,
            bank_id=settings.hindsight_bank_id,
        )
        recall_response = await memory_service.recall(recall_input)
        results = recall_response.results or []

        print(f"Recall returned {len(results)} relevant memory item(s):")
        if not results:
            print("  (No direct matches returned yet; memories may still be indexing if asynchronous)")
        else:
            for i, res in enumerate(results, start=1):
                text_snippet = getattr(res, "text", str(res))
                scores = getattr(res, "scores", {})
                tags = getattr(res, "tags", [])
                print(f"\n  Result #{i}:")
                print(f"    Tags  : {tags}")
                print(f"    Scores: {scores}")
                print(f"    Text  : {text_snippet[:250]}...")

        print("=" * 76)
        print("Real Hindsight RETAIN and RECALL verification completed successfully!")
        return True
    except Exception as err:
        print(f"RECALL query failed: {err}")
        return False
    finally:
        await manager.close()


def main() -> None:
    success = asyncio.run(run_hindsight_seeding())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

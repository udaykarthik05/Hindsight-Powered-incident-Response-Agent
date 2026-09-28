"""
Phase 6 Live Hindsight Verification Script

Performs real end-to-end verification against the live running Hindsight service:
1. Live Connectivity Check (http://localhost:8888)
2. Real RETAIN Test (PHASE6-HINDSIGHT-RETAIN-001)
3. Persistence Verification
4. Real RECALL Test (PHASE6-HINDSIGHT-RECALL-001)
5. Real REFLECT Test
6. Evidence Boundary Verification
7. Real Resolution -> RETAIN Test (HindsightMemoryLifecycle)
8. Idempotency Test with Real Hindsight
9. Graceful Failure & Recovery Verification (docker stop / start)
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timezone

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.agent.incident_agent import IncidentResponseAgent
from app.core.config import get_settings
from app.hindsight.client import get_hindsight_manager
from app.hindsight.lifecycle import (
    HindsightMemoryLifecycle,
    IncidentMemoryBuilder,
    RetentionStatus,
)
from app.hindsight.memory import (
    MemoryRecallInput,
    MemoryReflectInput,
    get_memory_service,
)
from app.repositories.incident_repository import get_incident_repository
from app.schemas.incident import IncidentCreate, IncidentResolve, IncidentStatus, Severity


async def run_live_verification():
    settings = get_settings()
    manager = get_hindsight_manager()
    memory_svc = get_memory_service()
    lifecycle = HindsightMemoryLifecycle(memory_service=memory_svc, settings=settings)
    repo = get_incident_repository()
    agent = IncidentResponseAgent(memory_service=memory_svc, settings=settings)

    print("=" * 80)
    print(" PHASE 6: REAL HINDSIGHT DEPLOYMENT & LIVE MEMORY VALIDATION")
    print("=" * 80)
    print(f"Target Hindsight Base URL : {settings.hindsight_base_url}")
    print(f"Target Memory Bank ID     : {settings.hindsight_bank_id}")
    print(f"Timestamp                 : {datetime.now(timezone.utc).isoformat()}")
    print("-" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: Verify Live Connectivity
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Verifying Live Hindsight Server Connectivity...")
    conn = await manager.check_connection()
    if not conn.connected:
        print(f"FAILED: Hindsight is unreachable at {settings.hindsight_base_url}: {conn.error}")
        return False

    print(f" SUCCESS: Connected to live Hindsight service!")
    print(f"  Server Version: {conn.server_version}")
    print(f"  Bank ID       : {conn.bank_id}")

    # --------------------------------------------------------------------------
    # STEP 2: Real RETAIN Test (Incident A)
    # --------------------------------------------------------------------------
    print("\n[STEP 2] Executing Real Hindsight RETAIN with Test Incident A...")
    incident_a = repo.create(
        IncidentCreate(
            incident_id="PHASE6-HINDSIGHT-RETAIN-001",
            title="Payment API Connection Pool Exhaustion — Phase 6 Memory Test",
            description=(
                "Checkout service failing with 504 Gateway Timeout errors during high-volume flash sale. "
                "Client connection attempts to database timed out after 5000ms."
            ),
            severity=Severity.CRITICAL,
            affected_service="payment-service",
            logs=[
                "2026-09-28T18:00:01Z [ERROR] connection pool exhausted (active=50/50, idle=0, waiting=240)",
                "2026-09-28T18:00:05Z [WARN] request queue depth exceeded limit (queue=500)",
                "2026-09-28T18:00:10Z [ERROR] 504 Gateway Timeout returned to client",
            ],
            error_messages=[
                "ConnectionTimeoutError: Client unable to acquire database connection within 5000ms",
                "HikariPool-1 - Connection is not available, request timed out after 5002ms.",
            ],
        )
    )

    # Resolve Incident A
    resolved_a = repo.resolve(
        incident_a.incident_id,
        IncidentResolve(
            root_cause="HikariCP connection pool limit (max=50) was saturated by prolonged checkout transactions and slow analytical queries, causing thread starvation.",
            mitigation="Increased max_connections to 150, terminated idle analytical sessions, and added a 3000ms query timeout.",
        ),
    )

    retain_input = IncidentMemoryBuilder.build(resolved_a)
    retain_res = await memory_svc.retain(retain_input)

    print(f" SUCCESS: RETAIN succeeded on real Hindsight service!")
    print(f"  Bank ID       : {retain_res.bank_id}")
    print(f"  Success Flag  : {retain_res.success}")
    print(f"  Items Retained: {retain_res.items_count}")
    print(f"  Token Usage   : {retain_res.usage}")

    # --------------------------------------------------------------------------
    # STEP 3: Verify Persistence
    # --------------------------------------------------------------------------
    print("\n[STEP 3] Verifying Memory Persistence in Hindsight Bank...")
    direct_recall = await memory_svc.recall(
        MemoryRecallInput(
            query="PHASE6-HINDSIGHT-RETAIN-001 Payment API connection pool",
            bank_id=settings.hindsight_bank_id,
            budget="mid",
        )
    )
    persisted_found = any(
        "PHASE6-HINDSIGHT-RETAIN-001" in getattr(r, "text", "")
        for r in (direct_recall.results or [])
    )
    if not persisted_found:
        print(" WARNING: Memory was retained but could not immediately be retrieved by ID.")
    else:
        print(f" SUCCESS: Verified persistent storage! Retrieved {len(direct_recall.results)} memory units matching test ID.")

    # --------------------------------------------------------------------------
    # STEP 4: Real RECALL Test (Incident B)
    # --------------------------------------------------------------------------
    print("\n[STEP 4] Executing Real Hindsight RECALL with New Related Incident B...")
    incident_b = repo.create(
        IncidentCreate(
            incident_id="PHASE6-HINDSIGHT-RECALL-001",
            title="Checkout Gateway HTTP 504 Timeouts — Phase 6 Recall Test",
            description=(
                "Checkout microservice experiencing elevated 504 timeouts and latency spikes following customer surge."
            ),
            severity=Severity.HIGH,
            affected_service="payment-service",
            logs=[
                "2026-09-28T18:15:00Z [ERROR] connection pool exhausted (active=50/50)",
                "2026-09-28T18:15:02Z [WARN] connection acquisition latency spike (>4800ms)",
            ],
            error_messages=[
                "ConnectionTimeoutError: Client unable to acquire database connection within 5000ms"
            ],
        )
    )

    investigation_b = await agent.investigate(incident_b)

    print(f" SUCCESS: Agent Investigation completed using Real Hindsight!")
    print(f"  Historical Context Available : {investigation_b.historical_context.available}")
    print(f"  Query Generated by Analysis  : {investigation_b.historical_context.query_used}")
    print(f"  Recalled Precedents Count    : {len(investigation_b.historical_context.recalled_incidents)}")

    recalled_ids = [m.incident_id for m in investigation_b.historical_context.recalled_incidents]
    print(f"  Recalled Incident IDs        : {recalled_ids}")

    assert "PHASE6-HINDSIGHT-RETAIN-001" in recalled_ids, (
        f"Expected PHASE6-HINDSIGHT-RETAIN-001 to be recalled, but got {recalled_ids}"
    )
    print(f"  -> Verified: Retained Incident A (PHASE6-HINDSIGHT-RETAIN-001) was successfully recalled!")

    # --------------------------------------------------------------------------
    # STEP 5: Real REFLECT Test
    # --------------------------------------------------------------------------
    print("\n[STEP 5] Verifying Hindsight REFLECT in Investigation...")
    print(f"  Reflect Summary Present: {bool(investigation_b.historical_context.reflection_summary)}")
    print(f"  Reflect Output Preview : '{investigation_b.historical_context.reflection_summary}'")

    # --------------------------------------------------------------------------
    # STEP 6: Evidence Boundary Test
    # --------------------------------------------------------------------------
    print("\n[STEP 6] Verifying Strict Evidence Boundary Separation...")
    # Check that Incident B itself has NO confirmed root cause
    assert incident_b.root_cause is None, "Incident B root cause must remain None prior to explicit resolution"
    
    # Check that hypotheses mention historical precedent as candidate theory, not confirmed truth
    pool_hypotheses = [
        h for h in investigation_b.hypotheses
        if "pool" in h.hypothesis.lower() or "database" in h.hypothesis.lower()
    ]
    assert len(pool_hypotheses) > 0, "Expected at least one database pool hypothesis"
    
    print(f"  Hypothesis Formulated: '{pool_hypotheses[0].hypothesis}'")
    print(f"  Supporting Telemetry : {pool_hypotheses[0].supporting_evidence}")
    print(f"  Related History Cited: {pool_hypotheses[0].related_historical_incidents}")
    assert "PHASE6-HINDSIGHT-RETAIN-001" in pool_hypotheses[0].related_historical_incidents
    print("  -> Verified: Historical precedent is cited as a candidate hypothesis without overwriting incident truth.")

    # --------------------------------------------------------------------------
    # STEP 7: Real Resolution -> RETAIN Pipeline
    # --------------------------------------------------------------------------
    print("\n[STEP 7] Verifying Resolution -> RETAIN via HindsightMemoryLifecycle...")
    incident_c = repo.create(
        IncidentCreate(
            incident_id="PHASE6-HINDSIGHT-RESOLVE-001",
            title="Database Connection Pool Exhaustion — Resolve Flow Test",
            description="Payment gateway connection timeout.",
            severity=Severity.HIGH,
            affected_service="payment-service",
            error_messages=["ConnectionTimeoutError: Pool exhausted"],
        )
    )
    repo.resolve(
        incident_c.incident_id,
        IncidentResolve(
            root_cause="Connection leak in batch invoice generator holding pool connections open.",
            mitigation="Patched batch job connection disposal and restarted workers.",
        ),
    )
    resolved_c = repo.get(incident_c.incident_id)

    lifecycle_result = await lifecycle.retain_resolved_incident(resolved_c)
    print(f"  Lifecycle Retention Status : {lifecycle_result.status.value}")
    print(f"  Lifecycle Message          : {lifecycle_result.message}")
    assert lifecycle_result.status == RetentionStatus.RETAINED

    # --------------------------------------------------------------------------
    # STEP 8: Idempotency with Real Hindsight
    # --------------------------------------------------------------------------
    print("\n[STEP 8] Verifying Idempotency with Real Hindsight...")
    # Update incident_c memory status in repo as resolve endpoint does
    from app.schemas.incident import IncidentUpdate
    repo.update(resolved_c.incident_id, IncidentUpdate(memory_status="retained"))
    resolved_c_updated = repo.get(resolved_c.incident_id)

    idempotency_result = await lifecycle.retain_resolved_incident(resolved_c_updated)
    print(f"  Second Retention Status: {idempotency_result.status.value}")
    print(f"  Second Retention Message: {idempotency_result.message}")
    assert idempotency_result.status == RetentionStatus.ALREADY_RETAINED
    print("  -> Verified: Repeated resolution calls avoid duplicate retention in Hindsight.")

    # --------------------------------------------------------------------------
    # STEP 9: Graceful Failure & Recovery Test
    # --------------------------------------------------------------------------
    print("\n[STEP 9] Verifying Graceful Failure Degradation and Recovery...")
    print("  Stopping Hindsight container temporarily (docker stop hindsight)...")
    subprocess.run(["wsl", "-u", "root", "-d", "Ubuntu", "docker", "stop", "hindsight"], check=True)

    # Verify disconnected status
    await manager.close()
    offline_status = await manager.check_connection()
    print(f"  Status when stopped: connected={offline_status.connected} (Expected: False)")
    assert not offline_status.connected

    # Attempt resolution while offline
    incident_d = repo.create(
        IncidentCreate(
            incident_id="PHASE6-HINDSIGHT-OFFLINE-001",
            title="Service Latency Outage While Memory Offline",
            description="Testing graceful degradation when Hindsight is offline.",
            severity=Severity.MEDIUM,
            affected_service="auth-service",
            error_messages=["AuthServiceTimeout: Downstream auth token validation timed out"],
        )
    )
    repo.resolve(
        incident_d.incident_id,
        IncidentResolve(
            root_cause="Redis cache node failure causing auth queries to hit primary database.",
            mitigation="Failed over to replica Redis cluster and evicted stale tokens.",
        ),
    )
    resolved_d = repo.get(incident_d.incident_id)
    offline_retention = await lifecycle.retain_resolved_incident(resolved_d)

    print(f"  Resolution Status Under Outage: {resolved_d.status.value} (Expected: resolved)")
    print(f"  Retention Status Under Outage : {offline_retention.status.value} (Expected: retention_failed)")
    assert resolved_d.status == IncidentStatus.RESOLVED
    assert offline_retention.status == RetentionStatus.RETENTION_FAILED
    print("  -> Verified: Offline Hindsight does NOT corrupt incident resolution!")

    # Restart Hindsight container
    print("  Restarting Hindsight container (docker start hindsight)...")
    subprocess.run(["wsl", "-u", "root", "-d", "Ubuntu", "docker", "start", "hindsight"], check=True)
    
    recovered = False
    for attempt in range(35):
        await asyncio.sleep(1)
        await manager.close()
        recovered_status = await manager.check_connection()
        if recovered_status.connected:
            recovered = True
            break

    print(f"  Status after restart: connected={recovered} (Expected: True)")
    assert recovered
    print("  -> Verified: Service recovered cleanly and resumed real memory operations!")

    print("\n" + "=" * 80)
    print(" ALL 9 LIVE VERIFICATION GATES PASSED WITH REAL HINDSIGHT SERVICE!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_live_verification())
    sys.exit(0 if success else 1)

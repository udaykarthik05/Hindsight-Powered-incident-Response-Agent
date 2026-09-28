import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000")

# 1. Create Incident A
inc_a = client.post("/api/v1/incidents", json={
    "title": "Stripe Webhook Processing Lag and Connection Saturation",
    "description": "Stripe webhook listener microservice experiencing DB pool starvation under volume.",
    "severity": "critical",
    "affected_service": "billing-service",
    "logs": ["HikariCP connection pool exhausted (active=50/50)", "Webhook processing worker timeout"],
    "error_messages": ["ConnectionTimeoutError: Pool exhausted after 5000ms"]
}).json()
id_a = inc_a["incident_id"]
print(f"Created Incident A: {id_a}")

# 2. Resolve Incident A
res_a = client.post(f"/api/v1/incidents/{id_a}/resolve", json={
    "root_cause": "HikariCP connection pool exhausted by long-running synchronous database queries in webhook handler.",
    "mitigation": "Bumped max pool size to 150 and converted webhook consumer to async pipeline."
}).json()
print(f"Resolved Incident A Status: {res_a['status']}")
print(f"Resolved Incident A Memory Status: {res_a.get('memory_status')}")
print(f"Resolved Incident A Memory Message: {res_a.get('memory_message')}")
assert res_a["memory_status"] == "retained", f"Expected retained, got {res_a.get('memory_status')}"

# 3. Create Related Incident B
inc_b = client.post("/api/v1/incidents", json={
    "title": "Billing Microservice 504 Gateway Timeouts",
    "description": "Webhook listener latency spike and database connection timeouts during invoice processing.",
    "severity": "high",
    "affected_service": "billing-service",
    "logs": ["connection pool exhausted (active=50/50)", "504 Gateway Timeout returned to webhook caller"],
    "error_messages": ["ConnectionTimeoutError: Client unable to acquire database connection within 5000ms"]
}).json()
id_b = inc_b["incident_id"]
print(f"Created Incident B: {id_b}")

# 4. Investigate Incident B
inv_b = client.post(f"/api/v1/incidents/{id_b}/investigate").json()
print("Investigation of Incident B:")
print(f"  Historical Available: {inv_b['historical_context']['available']}")
print(f"  Query Used: {inv_b['historical_context']['query_used']}")
print(f"  Recalled Count: {len(inv_b['historical_context']['recalled_incidents'])}")
recalled_ids = [m["incident_id"] for m in inv_b["historical_context"]["recalled_incidents"]]
print(f"  Recalled IDs: {recalled_ids}")
print(f"  Reflection Summary: {inv_b['historical_context']['reflection_summary']}")
found = id_a in recalled_ids or any(id_a in m.get("summary", "") for m in inv_b["historical_context"]["recalled_incidents"])
assert found, f"Incident A {id_a} not found in recalled memories"
print("  -> CONFIRMED: Incident A was retained, persisted in real Hindsight, and retrieved during Incident B investigation!")

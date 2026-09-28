from datetime import datetime, timezone
from typing import Any, Dict, List
from app.schemas.incident import Incident, IncidentStatus, Severity


class SeedIncidentPayload:
    """Wrapper holding an Incident along with historical metadata for Hindsight."""
    def __init__(self, incident: Incident, category: str, lessons_learned: str, tags: List[str]):
        self.incident = incident
        self.category = category
        self.lessons_learned = lessons_learned
        self.tags = tags

    def to_hindsight_format(self) -> Dict[str, Any]:
        """Convert into rich narrative format suitable for Hindsight RETAIN."""
        inc = self.incident
        content = (
            f"Historical Incident Report: {inc.incident_id} - {inc.title}\n"
            f"Service: {inc.affected_service} | Severity: {inc.severity.value.upper()} | Category: {self.category}\n"
            f"Occurred: {inc.timestamp.isoformat()} | Resolved: {inc.resolved_at.isoformat() if inc.resolved_at else 'N/A'}\n\n"
            f"SYMPTOMS & IMPACT:\n{inc.description}\n\n"
            f"OBSERVED LOGS & ERROR TRACES:\n" + "\n".join(f"  - {log}" for log in inc.logs) + "\n\n"
            f"ERROR MESSAGES:\n" + "\n".join(f"  - {err}" for err in inc.error_messages) + "\n\n"
            f"IDENTIFIED ROOT CAUSE:\n{inc.root_cause}\n\n"
            f"APPLIED MITIGATION & RESOLUTION:\n{inc.mitigation}\n\n"
            f"LESSONS LEARNED & PREVENTATIVE ACTIONS:\n{self.lessons_learned}"
        )
        metadata = {
            "incident_id": inc.incident_id,
            "service": inc.affected_service,
            "severity": inc.severity.value,
            "category": self.category,
            "status": inc.status.value,
        }
        return {
            "content": content,
            "context": f"Postmortem Incident Report {inc.incident_id}",
            "metadata": metadata,
            "tags": self.tags,
            "incident_id": inc.incident_id,
        }


def get_seed_data() -> List[SeedIncidentPayload]:
    """Return the curated list of 10 realistic historical software incidents."""
    return [
        # 1. Database connection pool exhaustion
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-101",
                title="Auth Service Database Connection Pool Exhaustion",
                description=(
                    "Users experienced severe latency and HTTP 504 Gateway Timeouts during morning login peak. "
                    "Auth service pods failed health probes and could not establish new database connections."
                ),
                severity=Severity.CRITICAL,
                affected_service="auth-service",
                timestamp=datetime(2025, 10, 14, 8, 15, 0, tzinfo=timezone.utc),
                logs=[
                    "2025-10-14 08:16:02 ERROR [pool.py:84] HikariPool-1 - Connection is not available, request timed out after 30005ms.",
                    "2025-10-14 08:16:15 ERROR [db.py:112] psycopg2.OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections",
                    "2025-10-14 08:16:22 WARN  [health.py:45] Health check failed for pod auth-service-78f99c85-2k9x: db ping timeout.",
                ],
                error_messages=[
                    "Connection is not available, request timed out after 30005ms.",
                    "psycopg2.OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "A regression in recent token validation middleware omitted connection context release on unhandled "
                    "HTTP exceptions, leaking connection slots under sustained morning traffic until the 100-connection limit was hit."
                ),
                mitigation=(
                    "Temporarily increased PostgreSQL max_connections to 250, rolled back token validation patch, "
                    "and wrapped database session handling in strict context manager with guaranteed finally block."
                ),
                created_at=datetime(2025, 10, 14, 8, 20, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2025, 10, 14, 9, 35, 0, tzinfo=timezone.utc),
            ),
            category="database connection pool exhaustion",
            lessons_learned=(
                "Implement proactive alerts at 80% connection pool utilization. "
                "Enforce linter rules prohibiting unmanaged raw DB sessions."
            ),
            tags=["database", "connection-pool", "postgres", "auth-service", "critical", "timeout"],
        ),

        # 2. Third-party payment gateway latency spike & worker thread starvation
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-102",
                title="Payment Gateway API Latency Spike & Cascading Worker Starvation",
                description=(
                    "Checkout completion failure rate spiked to 48%. Web frontends reported timeouts while "
                    "payment service worker threads were completely blocked waiting on external payment gateway."
                ),
                severity=Severity.CRITICAL,
                affected_service="payment-service",
                timestamp=datetime(2025, 11, 2, 14, 20, 0, tzinfo=timezone.utc),
                logs=[
                    "2025-11-02 14:21:10 ERROR [checkout.py:140] ReadTimeout: HTTPSConnectionPool(host='api.stripe-mock.internal', port=443): Read timed out. (read timeout=60.0)",
                    "2025-11-02 14:22:05 ERROR [server.py:202] ThreadPoolExecutor thread limit 64 exhausted. Rejecting incoming request /api/v1/charge.",
                    "2025-11-02 14:22:30 WARN  [gateway.py:88] Circuit breaker open for downstream payment processor.",
                ],
                error_messages=[
                    "ReadTimeout: HTTPSConnectionPool read timed out (read timeout=60.0)",
                    "ThreadPoolExecutor thread limit 64 exhausted",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "The upstream payment processor experienced network degradation causing 55s request latencies. "
                    "Our payment service had a default 60s socket timeout with no circuit breaker, causing all 64 "
                    "worker threads to become saturated within 90 seconds."
                ),
                mitigation=(
                    "Reduced external client timeout to 5.0s, introduced an active circuit breaker with exponential backoff, "
                    "and segregated payment processing into an asynchronous job queue."
                ),
                created_at=datetime(2025, 11, 2, 14, 25, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2025, 11, 2, 15, 45, 0, tzinfo=timezone.utc),
            ),
            category="API latency spike",
            lessons_learned=(
                "All external third-party HTTP calls must have strict timeouts (< 5s) and circuit breakers. "
                "Never block synchronous web workers on external third parties."
            ),
            tags=["payment", "latency", "external-api", "thread-starvation", "circuit-breaker", "critical"],
        ),

        # 3. Expired JWT signing key
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-103",
                title="Expired JWT Signing Key Causing Global Authentication Rejection",
                description=(
                    "All authenticated requests across API Gateway failed with HTTP 401 Unauthorized. "
                    "Users were logged out en masse across mobile and web platforms."
                ),
                severity=Severity.CRITICAL,
                affected_service="api-gateway",
                timestamp=datetime(2025, 11, 19, 0, 0, 10, tzinfo=timezone.utc),
                logs=[
                    "2025-11-19 00:00:15 ERROR [jwt_verifier.go:73] jwt.exceptions.ExpiredSignatureError: Signature has expired for keyId 'auth-key-2024-q4'",
                    "2025-11-19 00:00:18 ERROR [auth_middleware.go:102] KeyVerificationError: Unable to verify token signature: key expired at 2025-11-19T00:00:00Z",
                    "2025-11-19 00:00:30 WARN  [gateway.go:310] Rejection rate exceeded threshold: 99.4% requests returning 401.",
                ],
                error_messages=[
                    "jwt.exceptions.ExpiredSignatureError: Signature has expired",
                    "KeyVerificationError: Unable to verify signature with keyId 'auth-key-2024-q4'",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "An automated cryptographic key rotation cron job failed 7 days prior due to an AWS IAM permission "
                    "boundary change. The existing key reached its absolute expiry without a secondary valid key present in JWKS."
                ),
                mitigation=(
                    "Manually generated and pushed new key pair to JWKS endpoint, updated IAM policy for the automated "
                    "rotator, and issued a rolling restart of API Gateway proxies to clear cached keys."
                ),
                created_at=datetime(2025, 11, 19, 0, 5, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2025, 11, 19, 0, 48, 0, tzinfo=timezone.utc),
            ),
            category="authentication failure",
            lessons_learned=(
                "Add dual-key overlap periods of at least 14 days during key rotation. "
                "Monitor key expiration dates with Prometheus alert 14, 7, and 3 days before TTL."
            ),
            tags=["auth", "jwt", "gateway", "security", "keys", "critical"],
        ),

        # 4. Redis cluster eviction storm & memory OOM
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-104",
                title="Redis Cluster Eviction Storm & Memory OOM Lockup",
                description=(
                    "Cache hit ratio dropped from 94% to 8%, causing catastrophic 5x read load on primary databases. "
                    "Redis nodes reported 100% CPU and refused new writes."
                ),
                severity=Severity.HIGH,
                affected_service="cache-service",
                timestamp=datetime(2025, 12, 5, 11, 10, 0, tzinfo=timezone.utc),
                logs=[
                    "2025-12-05 11:10:45 ERROR [redis_client.py:90] OOM command not allowed when used memory > 'maxmemory'",
                    "2025-12-05 11:11:12 ERROR [session_cache.py:44] redis.exceptions.ResponseError: Command timed out after 2000ms",
                    "2025-12-05 11:11:30 WARN  [cluster.py:112] Eviction policy 'noeviction' rejected write on key 'search_index:v2:994821'.",
                ],
                error_messages=[
                    "OOM command not allowed when used memory > 'maxmemory'",
                    "redis.exceptions.ResponseError: Command timed out after 2000ms",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "A product catalog search release populated keys without TTL expirations into a Redis cluster configured "
                    "with 'noeviction' policy. Memory reached the 16GB ceiling, rejecting all write commands."
                ),
                mitigation=(
                    "Switched eviction policy dynamically to 'volatile-lru', ran background SCAN script to purge "
                    "untagged catalog keys, and deployed a code patch strictly enforcing mandatory TTL on all Redis sets."
                ),
                created_at=datetime(2025, 12, 5, 11, 15, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2025, 12, 5, 12, 20, 0, tzinfo=timezone.utc),
            ),
            category="Redis/cache outage",
            lessons_learned=(
                "Never configure caching tiers with 'noeviction' policy. "
                "Enforce TTL in the caching client wrapper so keys cannot be written without expiration."
            ),
            tags=["redis", "cache", "oom", "eviction", "high", "memory"],
        ),

        # 5. Deployment regression: migration table lock
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-105",
                title="Deployment Regression: Malformed Migration Locks User Table",
                description=(
                    "Following v2.4.0 deployment, all user profile updates and registrations hung indefinitely. "
                    "Database active queries spiked to hundreds of blocked transactions."
                ),
                severity=Severity.CRITICAL,
                affected_service="user-service",
                timestamp=datetime(2025, 12, 18, 19, 0, 0, tzinfo=timezone.utc),
                logs=[
                    "2025-12-18 19:01:22 ERROR [django.db:55] django.db.utils.OperationalError: Lock wait timeout exceeded; try restarting transaction",
                    "2025-12-18 19:02:00 ERROR [models.py:130] PostgreSQL query waiting for AccessExclusiveLock on relation 'users'",
                    "2025-12-18 19:02:40 WARN  [pool.py:90] High pool wait queue length: 280 threads waiting.",
                ],
                error_messages=[
                    "django.db.utils.OperationalError: Lock wait timeout exceeded",
                    "PostgreSQL query waiting for AccessExclusiveLock on relation 'users'",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "An Alembic migration script attempted an ALTER TABLE users ADD COLUMN preferences JSON DEFAULT '{}' "
                    "without PostgreSQL optimization, requiring an exclusive table lock on 12 million rows during peak hours."
                ),
                mitigation=(
                    "Terminated the blocking DDL migration backend PID (`pg_terminate_backend`), rolled back deployment, "
                    "and reapplied the migration using nullable column addition followed by asynchronous backfill."
                ),
                created_at=datetime(2025, 12, 18, 19, 5, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2025, 12, 18, 19, 40, 0, tzinfo=timezone.utc),
            ),
            category="deployment regression",
            lessons_learned=(
                "Mandate zero-downtime migration linters in CI pipeline (e.g., strong_migrations). "
                "Never add columns with non-constant defaults on multi-million row tables synchronously."
            ),
            tags=["deployment", "database", "migration", "locks", "postgres", "critical"],
        ),

        # 6. Memory leak in background worker
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-106",
                title="Memory Leak in Background Async Notification Worker",
                description=(
                    "Notification delivery latency escalated from seconds to hours. "
                    "Background worker nodes systematically crashed and restarted due to Linux OOM-killer."
                ),
                severity=Severity.MEDIUM,
                affected_service="notification-service",
                timestamp=datetime(2026, 1, 8, 4, 30, 0, tzinfo=timezone.utc),
                logs=[
                    "2026-01-08 04:31:00 ERROR [kernel:8012] Out of memory: Kill process 41829 (celery) score 920 or sacrifice child",
                    "2026-01-08 04:31:02 ERROR [kernel:8013] Killed process 41829 (celery) total-vm:4294967kB, anon-rss:3670016kB",
                    "2026-01-08 04:32:15 WARN  [celery.worker:88] Worker node notification-worker-3 disconnected abruptly; re-queuing 450 tasks.",
                ],
                error_messages=[
                    "Out of memory: Kill process 41829 (celery)",
                    "Worker node disconnected abruptly; re-queuing tasks",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "A customized Jinja2 email template environment was instantiated inside each task execution and "
                    "stored template bytecode in an unbounded module-level dictionary cache, consuming 4GB RAM within 48 hours."
                ),
                mitigation=(
                    "Refactored template rendering to reuse a single shared Jinja2 Environment instance, and enabled "
                    "`--max-tasks-per-child=1000` to automatically recycle worker processes and eliminate RAM leakage."
                ),
                created_at=datetime(2026, 1, 8, 4, 35, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 1, 8, 6, 15, 0, tzinfo=timezone.utc),
            ),
            category="memory leak",
            lessons_learned=(
                "Worker processes must always have recycle limits (`max-tasks-per-child`). "
                "Profile memory consumption in staging for asynchronous background tasks."
            ),
            tags=["memory-leak", "celery", "workers", "notifications", "oom", "medium"],
        ),

        # 7. Disk space exhaustion on logging volume
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-107",
                title="Disk Space Exhaustion on Logging Volume Halting Ingestion",
                description=(
                    "Audit log ingestion pods crashed and went into CrashLoopBackOff. "
                    "Write requests were rejected with POSIX Errno 28 (No space left on device)."
                ),
                severity=Severity.HIGH,
                affected_service="audit-service",
                timestamp=datetime(2026, 1, 22, 16, 45, 0, tzinfo=timezone.utc),
                logs=[
                    "2026-01-22 16:45:10 ERROR [ingest.py:210] IOError: [Errno 28] No space left on device: '/var/log/audit/events.log'",
                    "2026-01-22 16:45:22 ERROR [buffer.py:89] WriteFailedException: unable to write chunk to disk buffer on volume /data",
                    "2026-01-22 16:46:00 FATAL [server.py:55] Audit worker terminating: storage disk full (100% capacity reached).",
                ],
                error_messages=[
                    "IOError: [Errno 28] No space left on device: '/var/log/audit/events.log'",
                    "Audit worker terminating: storage disk full",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "Logrotate daemon failed due to a typo in a configuration update (`/etc/logrotate.d/audit`). "
                    "Combined with a debug log level accidentally left enabled in production, the disk filled up in 6 hours."
                ),
                mitigation=(
                    "Flushed older compressed logs to S3 cold storage, corrected the logrotate syntax error, "
                    "and restored default INFO log level via dynamic config reload."
                ),
                created_at=datetime(2026, 1, 22, 16, 50, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 1, 22, 17, 30, 0, tzinfo=timezone.utc),
            ),
            category="disk/storage exhaustion",
            lessons_learned=(
                "Isolate log partitions from application data volumes. "
                "Set disk alerts at 75% and 85% with automated log rotation syntax validation in CI."
            ),
            tags=["disk", "storage", "logging", "crashloop", "high"],
        ),

        # 8. CoreDNS packet drops & service discovery failure
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-108",
                title="CoreDNS Packet Drops Causing Intermittent Service Discovery Failures",
                description=(
                    "Approximately 6% of internal inter-service gRPC and REST requests failed with 'Name or service not known'. "
                    "Services experienced cascading retries and increased response latencies."
                ),
                severity=Severity.HIGH,
                affected_service="order-service",
                timestamp=datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
                logs=[
                    "2026-02-04 10:01:12 ERROR [http_client.go:88] gaierror: [Errno -2] Name or service not known for order-service.production.svc.cluster.local",
                    "2026-02-04 10:01:25 ERROR [resolver.go:42] CoreDNS: 53 udp: i/o timeout resolving inventory-service",
                    "2026-02-04 10:02:00 WARN  [kube-proxy:104] Conntrack table high watermark exceeded: 96% entries occupied.",
                ],
                error_messages=[
                    "gaierror: [Errno -2] Name or service not known",
                    "CoreDNS: 53 udp: i/o timeout resolving inventory-service",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "CoreDNS cluster was under-provisioned (only 2 replicas for 900 pods). During a traffic burst, "
                    "UDP DNS lookups saturated Linux conntrack tables, causing silent packet drops on name resolution."
                ),
                mitigation=(
                    "Scaled CoreDNS replicas from 2 to 8 with horizontal pod autoscaling, and rolled out NodeLocal DNSCache "
                    "daemonset to handle DNS caching locally on every Kubernetes node without UDP conntrack contention."
                ),
                created_at=datetime(2026, 2, 4, 10, 5, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 2, 4, 11, 10, 0, tzinfo=timezone.utc),
            ),
            category="DNS/service discovery failure",
            lessons_learned=(
                "Deploy NodeLocal DNSCache in all production Kubernetes clusters. "
                "Monitor Linux conntrack table saturation and scale CoreDNS based on cluster pod density."
            ),
            tags=["dns", "coredns", "networking", "kubernetes", "service-discovery", "high"],
        ),

        # 9. Dead Letter Queue (DLQ) overflow in Kafka consumer
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-109",
                title="Dead Letter Queue (DLQ) Overflow in Kafka Event Consumer",
                description=(
                    "Warehouse inventory synchronization lagged by over 5 hours. Over 60,000 order stock events "
                    "were routed into the DLQ, halting automated stock deductions."
                ),
                severity=Severity.HIGH,
                affected_service="inventory-service",
                timestamp=datetime(2026, 2, 17, 13, 15, 0, tzinfo=timezone.utc),
                logs=[
                    "2026-02-17 13:16:02 ERROR [consumer.py:112] DeserializationException: Payload contains unexpected null field: 'warehouse_code'",
                    "2026-02-17 13:16:15 WARN  [dlq_producer.py:45] Record moved to DLQ: inventory.events.dlq (offset: 8941028)",
                    "2026-02-17 13:17:00 ERROR [monitor.py:78] Consumer lag on topic 'order.events' exceeded 50,000 records.",
                ],
                error_messages=[
                    "DeserializationException: Payload contains unexpected null field: 'warehouse_code'",
                    "Consumer lag on topic 'order.events' exceeded 50,000 records",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "The checkout service deployed a payload change that made 'warehouse_code' optional without updating "
                    "the Schema Registry backwards compatibility rules. The inventory consumer strictly expected a non-null string."
                ),
                mitigation=(
                    "Patched inventory consumer with fallback default warehouse mapping for null fields, deployed hotfix, "
                    "and executed a safe DLQ replay script to reprocess 62,000 diverted events."
                ),
                created_at=datetime(2026, 2, 17, 13, 20, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 2, 17, 15, 0, 0, tzinfo=timezone.utc),
            ),
            category="message queue backlog",
            lessons_learned=(
                "Enforce strict Schema Registry compatibility checks (FULL/BACKWARD) in CI pipelines. "
                "Never break event field contracts between producers and consumers without deprecation cycles."
            ),
            tags=["kafka", "queue", "dlq", "serialization", "inventory", "high"],
        ),

        # 10. SSL/TLS Certificate expiration on internal load balancer
        SeedIncidentPayload(
            incident=Incident(
                incident_id="INC-2025-110",
                title="SSL/TLS Certificate Expiration on Internal Load Balancer",
                description=(
                    "All internal microservice calls to the billing API failed immediately with SSL handshake errors. "
                    "Subscription renewals and invoice generation halted across the company."
                ),
                severity=Severity.CRITICAL,
                affected_service="billing-service",
                timestamp=datetime(2026, 3, 3, 7, 0, 0, tzinfo=timezone.utc),
                logs=[
                    "2026-03-03 07:01:05 ERROR [transport.py:120] SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired (_ssl.c:1129)",
                    "2026-03-03 07:01:20 ERROR [client.py:65] HTTPSConnectionPool(host='billing.internal.company.com', port=443): Max retries exceeded with url: /invoices",
                    "2026-03-03 07:02:00 FATAL [lb.go:95] TLS Handshake failed: client 10.0.4.15 terminated handshake due to expired certificate.",
                ],
                error_messages=[
                    "SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired",
                    "TLS Handshake failed: client terminated handshake due to expired certificate",
                ],
                status=IncidentStatus.RESOLVED,
                root_cause=(
                    "Internal cert-manager ingress annotation was inadvertently deleted during Helm chart refactoring. "
                    "The internal TLS certificate reached its 90-day validity expiration without automated renewal."
                ),
                mitigation=(
                    "Manually re-issued certificate through internal CA, restored cert-manager renewal annotation, "
                    "and deployed Prometheus blackbox certificate exporter alerting 30, 14, and 7 days prior to expiry."
                ),
                created_at=datetime(2026, 3, 3, 7, 5, 0, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 3, 3, 7, 45, 0, tzinfo=timezone.utc),
            ),
            category="third-party/TLS failure",
            lessons_learned=(
                "Monitor TLS certificate expiration dates for all internal services, not just external domains. "
                "Set multi-tier alerts at 30 days and 14 days before certificate expiration."
            ),
            tags=["tls", "ssl", "certificate", "security", "billing", "critical"],
        ),
    ]


def get_seed_incidents() -> List[Incident]:
    """Helper returning pure Incident objects from the seed dataset."""
    return [payload.incident for payload in get_seed_data()]

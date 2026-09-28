import re
from typing import Dict, List, Set, Tuple
from app.agent.models import ObservedSignals
from app.schemas.incident import Incident


class DeterministicAnalyzer:
    """
    Deterministic rule-based initial analysis layer.
    
    Extracts structured technical signals from incident text, logs, and error messages
    before handing context off to Hindsight and the LLM.
    """

    # Keyword and regex patterns for technical classifications
    ERROR_PATTERNS: Dict[str, List[str]] = {
        "504_gateway_timeout": [r"504\s+gateway\s+timeout", r"gateway\s+timeout", r"http\s+504"],
        "502_bad_gateway": [r"502\s+bad\s+gateway", r"bad\s+gateway", r"http\s+502"],
        "connection_refused": [r"connection\s+refused", r"refused\s+the\s+network\s+connection"],
        "read_timeout": [r"read\s+timed?\s*out", r"readtimeout", r"socket\s+timeout"],
        "connect_timeout": [r"connect\s+timed?\s*out", r"request\s+timed\s+out\s+after"],
        "database_operational_error": [r"operationalerror", r"psycopg2\.operationalerror", r"remaining\s+connection\s+slots"],
        "connection_pool_exhaustion": [r"connection\s+is\s+not\s+available", r"pool.*exhausted", r"hikaripool"],
        "lock_wait_timeout": [r"lock\s+wait\s+timeout", r"accessclusivelock", r"deadlock\s+detected"],
        "out_of_memory": [r"out\s+of\s+memory", r"oom", r"kill\s+process.*celery", r"maxmemory"],
        "jwt_expired": [r"expiredsignatureerror", r"signature\s+has\s+expired", r"keyverificationerror", r"401\s+unauthorized"],
        "ssl_cert_expired": [r"certificate\s+has\s+expired", r"certificate_verify_failed", r"sslerror"],
        "dns_resolution_failure": [r"name\s+or\s+service\s+not\s+known", r"gaierror", r"coredns.*timeout"],
        "kafka_deserialization_error": [r"deserializationexception", r"moved\s+to\s+dlq", r"consumer\s+lag"],
        "disk_space_exhaustion": [r"no\s+space\s+left\s+on\s+device", r"errno\s+28", r"storage\s+disk\s+full"],
    }

    INFRASTRUCTURE_PATTERNS: Dict[str, List[str]] = {
        "database": ["postgres", "postgresql", "mysql", "database", "psycopg2", "query", "relation", "sql", "db"],
        "connection_pool": ["connection pool", "pool", "max_connections", "hikari", "pool-1", "connection slots"],
        "redis_cache": ["redis", "cache", "eviction", "noeviction", "volatile-lru", "session_cache"],
        "api_gateway": ["gateway", "ingress", "api-gateway", "proxy", "nginx", "envoy"],
        "payment_gateway": ["stripe", "payment", "charge", "checkout", "billing", "invoice"],
        "message_queue": ["kafka", "queue", "dlq", "celery", "worker", "consumer", "topic"],
        "auth_security": ["jwt", "token", "auth", "authentication", "jwks", "signature", "keyid"],
        "dns_network": ["dns", "coredns", "conntrack", "udp", "socket", "network", "grpc"],
        "tls_certificate": ["ssl", "tls", "certificate", "cert-manager", "handshake", "ca"],
        "storage_logging": ["logrotate", "disk", "storage", "volume", "partition", "audit"],
    }

    DEPLOYMENT_KEYWORDS: List[str] = [
        "deploy", "deployment", "migration", "release", "rollout", "version",
        "alembic", "patch", "updated", "commit", "v1.", "v2.", "recently deployed",
    ]

    @classmethod
    def analyze(cls, incident: Incident) -> Tuple[ObservedSignals, str]:
        """
        Analyze current incident evidence and generate deterministic signals
        along with an optimized search query for Hindsight RECALL.
        """
        # Combine all incident text for analysis
        text_corpus = " ".join([
            incident.title,
            incident.description,
            incident.affected_service,
            " ".join(incident.logs),
            " ".join(incident.error_messages),
        ]).lower()

        # 1. Detect error patterns
        matched_error_keys: Set[str] = set()
        matched_errors: List[str] = []
        for error_type, patterns in cls.ERROR_PATTERNS.items():
            if any(re.search(pattern, text_corpus, re.IGNORECASE) for pattern in patterns):
                matched_error_keys.add(error_type)
                matched_errors.append(error_type.replace("_", " ").title())

        # 2. Detect infrastructure components
        matched_component_keys: Set[str] = set()
        matched_components: List[str] = []
        for component, keywords in cls.INFRASTRUCTURE_PATTERNS.items():
            if any(kw in text_corpus for kw in keywords):
                matched_component_keys.add(component)
                matched_components.append(component.replace("_", " "))

        # 3. Detect deployment correlation
        deployment_correlated = any(
            re.search(rf"\b{re.escape(kw)}\b", text_corpus, re.IGNORECASE)
            for kw in cls.DEPLOYMENT_KEYWORDS
        )

        # 4. Infer suspected incident categories
        suspected_categories: List[str] = []
        if "connection_pool" in matched_component_keys or "connection_pool_exhaustion" in matched_error_keys:
            suspected_categories.append("Database Connection Pool Exhaustion")
        if (
            "read_timeout" in matched_error_keys
            or "connect_timeout" in matched_error_keys
            or "504_gateway_timeout" in matched_error_keys
        ):
            suspected_categories.append("API Latency & Timeout Spike")
        if "jwt_expired" in matched_error_keys or "auth_security" in matched_component_keys:
            suspected_categories.append("Authentication / Key Expiry Failure")
        if "redis_cache" in matched_component_keys:
            suspected_categories.append("Redis / Cache Outage")
        if deployment_correlated and ("migration" in text_corpus or "lock_wait_timeout" in matched_error_keys):
            suspected_categories.append("Deployment Regression (Schema Migration Lock)")
        elif deployment_correlated:
            suspected_categories.append("Deployment Regression")
        if "out_of_memory" in matched_error_keys:
            suspected_categories.append("Memory Leak / OOM Failure")
        if "disk_space_exhaustion" in matched_error_keys or "storage_logging" in matched_component_keys:
            suspected_categories.append("Disk / Storage Exhaustion")
        if "dns_resolution_failure" in matched_error_keys or "dns_network" in matched_component_keys:
            suspected_categories.append("DNS / Service Discovery Failure")
        if "kafka_deserialization_error" in matched_error_keys or "message_queue" in matched_component_keys:
            suspected_categories.append("Message Queue / DLQ Backlog")
        if "ssl_cert_expired" in matched_error_keys:
            suspected_categories.append("TLS / SSL Certificate Expiration")

        # 5. Extract technical keywords
        raw_words = re.findall(r"\b[a-zA-Z0-9_\-\.]{4,}\b", text_corpus)
        stopwords = {
            "this", "that", "with", "from", "after", "were", "have", "been", "failed",
            "error", "incident", "service", "status", "reported", "users", "server",
        }
        word_freq: Dict[str, int] = {}
        for w in raw_words:
            if w not in stopwords and not w.isdigit():
                word_freq[w] = word_freq.get(w, 0) + 1
        top_keywords = [
            w for w, _ in sorted(word_freq.items(), key=lambda item: item[1], reverse=True)[:8]
        ]

        signals = ObservedSignals(
            affected_service=incident.affected_service,
            error_types=matched_errors,
            infrastructure_components=matched_components,
            suspected_categories=suspected_categories or ["General System Degradation"],
            deployment_correlated=deployment_correlated,
            extracted_keywords=top_keywords,
        )

        # 6. Construct targeted Hindsight RECALL query
        query_elements = [f"Service: {incident.affected_service}"]
        if suspected_categories:
            query_elements.append(f"Category: {', '.join(suspected_categories[:2])}")
        if matched_errors:
            query_elements.append(f"Errors: {', '.join(matched_errors[:3])}")
        if matched_components:
            query_elements.append(f"Components: {', '.join(matched_components[:3])}")

        recall_query = (
            f"Find historical incidents for {incident.affected_service} with symptoms: "
            f"{', '.join(query_elements)}. "
            f"Keywords: {', '.join(top_keywords[:4])}."
        )

        return signals, recall_query

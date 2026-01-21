"""Prometheus metrics collection."""
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# API Metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

api_errors_total = Counter(
    "api_errors_total",
    "Total API errors",
    ["method", "endpoint", "error_type"],
)

# Neo4j Metrics
neo4j_queries_total = Counter(
    "neo4j_queries_total",
    "Total Neo4j queries",
    ["query_type"],
)

neo4j_query_duration_seconds = Histogram(
    "neo4j_query_duration_seconds",
    "Neo4j query duration in seconds",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0],
)

neo4j_connection_pool_size = Gauge(
    "neo4j_connection_pool_size",
    "Neo4j connection pool size",
)

neo4j_connection_pool_active = Gauge(
    "neo4j_connection_pool_active",
    "Active Neo4j connections",
)

# Cache Metrics
cache_requests_total = Counter(
    "cache_requests_total",
    "Total cache requests",
    ["cache_type", "operation"],
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["cache_type", "operation"],
)

# Ingestion Metrics
ingestion_jobs_total = Counter(
    "ingestion_jobs_total",
    "Total ingestion jobs",
    ["job_type", "status"],
)

ingestion_job_duration_seconds = Histogram(
    "ingestion_job_duration_seconds",
    "Ingestion job duration in seconds",
    ["job_type"],
)

ingestion_records_processed = Counter(
    "ingestion_records_processed",
    "Total records processed",
    ["job_type", "status"],
)

# Risk Metrics
risk_calculations_total = Counter(
    "risk_calculations_total",
    "Total risk calculations",
    ["business_id"],
)

risk_calculation_duration_seconds = Histogram(
    "risk_calculation_duration_seconds",
    "Risk calculation duration in seconds",
)

high_risk_businesses = Gauge(
    "high_risk_businesses",
    "Number of high-risk businesses",
)

# Fraud Metrics
fraud_alerts_total = Counter(
    "fraud_alerts_total",
    "Total fraud alerts",
    ["severity", "pattern_type"],
)

fraud_detection_duration_seconds = Histogram(
    "fraud_detection_duration_seconds",
    "Fraud detection duration in seconds",
)

# Workflow Metrics
workflow_approvals_total = Counter(
    "workflow_approvals_total",
    "Total workflow approvals",
    ["workflow_type", "status"],
)

workflow_approval_duration_seconds = Histogram(
    "workflow_approval_duration_seconds",
    "Workflow approval duration in seconds",
    ["workflow_type"],
)

pending_workflows = Gauge(
    "pending_workflows",
    "Number of pending workflows",
)

# System Metrics
system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
)

system_memory_usage = Gauge(
    "system_memory_usage_bytes",
    "System memory usage in bytes",
)

system_disk_usage = Gauge(
    "system_disk_usage_bytes",
    "System disk usage in bytes",
)

# Search Metrics
search_queries_total = Counter(
    "search_queries_total",
    "Total search queries",
    ["index", "query_type"],
)

search_query_duration_seconds = Histogram(
    "search_query_duration_seconds",
    "Search query duration in seconds",
    ["index"],
)


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get content type for metrics endpoint."""
    return CONTENT_TYPE_LATEST

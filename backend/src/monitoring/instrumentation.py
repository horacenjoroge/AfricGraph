"""Metrics instrumentation helpers for services."""
import time
from contextlib import contextmanager
from typing import Optional

from src.monitoring.metrics import (
    neo4j_queries_total,
    neo4j_query_duration_seconds,
    cache_requests_total,
    cache_hits_total,
    cache_misses_total,
    cache_operations_duration_seconds,
    risk_calculations_total,
    risk_calculation_duration_seconds,
    fraud_alerts_total,
    fraud_detection_duration_seconds,
    workflow_approvals_total,
    workflow_approval_duration_seconds,
    ingestion_jobs_total,
    ingestion_job_duration_seconds,
    ingestion_records_processed,
    search_queries_total,
    search_query_duration_seconds,
)


@contextmanager
def track_neo4j_query(query_type: str = "cypher"):
    """Track Neo4j query execution."""
    start_time = time.time()
    try:
        yield
        neo4j_queries_total.labels(query_type=query_type).inc()
    finally:
        duration = time.time() - start_time
        neo4j_query_duration_seconds.labels(query_type=query_type).observe(duration)


@contextmanager
def track_cache_operation(cache_type: str, operation: str, hit: Optional[bool] = None):
    """Track cache operation."""
    start_time = time.time()
    cache_requests_total.labels(cache_type=cache_type, operation=operation).inc()
    try:
        yield
    finally:
        duration = time.time() - start_time
        cache_operations_duration_seconds.labels(
            cache_type=cache_type, operation=operation
        ).observe(duration)

        if hit is True:
            cache_hits_total.labels(cache_type=cache_type).inc()
        elif hit is False:
            cache_misses_total.labels(cache_type=cache_type).inc()


@contextmanager
def track_risk_calculation(business_id: Optional[str] = None):
    """Track risk calculation."""
    start_time = time.time()
    try:
        yield
        if business_id:
            risk_calculations_total.labels(business_id=business_id).inc()
    finally:
        duration = time.time() - start_time
        risk_calculation_duration_seconds.observe(duration)


@contextmanager
def track_fraud_detection():
    """Track fraud detection."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        fraud_detection_duration_seconds.observe(duration)


def record_fraud_alert(severity: str, pattern_type: str):
    """Record a fraud alert."""
    fraud_alerts_total.labels(severity=severity, pattern_type=pattern_type).inc()


@contextmanager
def track_workflow_approval(workflow_type: str):
    """Track workflow approval."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        workflow_approval_duration_seconds.labels(workflow_type=workflow_type).observe(
            duration
        )


def record_workflow_approval(workflow_type: str, status: str):
    """Record workflow approval."""
    workflow_approvals_total.labels(workflow_type=workflow_type, status=status).inc()


@contextmanager
def track_ingestion_job(job_type: str):
    """Track ingestion job."""
    start_time = time.time()
    try:
        yield
        ingestion_jobs_total.labels(job_type=job_type, status="success").inc()
    except Exception:
        ingestion_jobs_total.labels(job_type=job_type, status="failure").inc()
        raise
    finally:
        duration = time.time() - start_time
        ingestion_job_duration_seconds.labels(job_type=job_type).observe(duration)


def record_ingestion_records(job_type: str, count: int, status: str = "success"):
    """Record processed ingestion records."""
    ingestion_records_processed.labels(job_type=job_type, status=status).inc(count)


@contextmanager
def track_search_query(index: str, query_type: str = "fulltext"):
    """Track search query."""
    start_time = time.time()
    search_queries_total.labels(index=index, query_type=query_type).inc()
    try:
        yield
    finally:
        duration = time.time() - start_time
        search_query_duration_seconds.labels(index=index).observe(duration)

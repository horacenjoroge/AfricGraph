"""Ingestion job status tracking (PostgreSQL)."""
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client

TABLE = "ingestion_jobs"
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_DLQ = "dlq"


def ensure_ingestion_jobs_table() -> None:
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        source VARCHAR(50) NOT NULL,
        source_params JSONB NOT NULL DEFAULT '{{}}',
        status VARCHAR(20) NOT NULL DEFAULT '{STATUS_PENDING}',
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        error_message TEXT,
        stats JSONB DEFAULT '{{}}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON {TABLE}(status);
    CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_created_at ON {TABLE}(created_at DESC);
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def _serialize(v: Any) -> Any:
    if isinstance(v, (datetime,)):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    return v


def create_job(source: str, source_params: Optional[Dict[str, Any]] = None) -> str:
    params = source_params or {}
    payload = json.dumps({k: _serialize(v) for k, v in params.items()}, default=str)
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            INSERT INTO {TABLE} (source, source_params, status)
            VALUES (:source, CAST(:params AS jsonb), :status)
            RETURNING id
            """),
            {"source": source, "params": payload, "status": STATUS_PENDING},
        )
        (jid,) = r.fetchone()
    return str(jid)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            SELECT id, source, source_params, status, started_at, finished_at, error_message, stats, created_at
            FROM {TABLE} WHERE id = :id
            """),
            {"id": job_id},
        )
        row = r.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "source": row[1],
        "source_params": row[2] or {},
        "status": row[3],
        "started_at": row[4],
        "finished_at": row[5],
        "error_message": row[6],
        "stats": row[7] or {},
        "created_at": row[8],
    }


def update_job_status(
    job_id: str,
    status: str,
    error_message: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None,
) -> None:
    updates = ["status = :status"]
    params = {"id": job_id, "status": status}
    if status == STATUS_RUNNING:
        updates.append("started_at = coalesce(started_at, now())")
    if status in (STATUS_SUCCESS, STATUS_FAILED, STATUS_DLQ):
        updates.append("finished_at = now()")
    if error_message is not None:
        updates.append("error_message = :error_message")
        params["error_message"] = error_message
    if stats is not None:
        updates.append("stats = CAST(:stats AS jsonb)")
        params["stats"] = json.dumps(stats, default=str)
    with postgres_client.get_session() as s:
        s.execute(text(f"UPDATE {TABLE} SET {', '.join(updates)} WHERE id = :id"), params)


def list_jobs(limit: int = 100, status: Optional[str] = None) -> list[Dict[str, Any]]:
    """List ingestion jobs, optionally filtered by status."""
    query = f"""
    SELECT id, source, source_params, status, started_at, finished_at, error_message, stats, created_at
    FROM {TABLE}
    """
    params = {"limit": limit}
    if status:
        query += " WHERE status = :status"
        params["status"] = status
    query += " ORDER BY created_at DESC LIMIT :limit"
    
    with postgres_client.get_session() as s:
        r = s.execute(text(query), params)
        rows = r.fetchall()
    
    return [
        {
            "job_id": str(row[0]),
            "job_type": row[1],
            "source_params": row[2] or {},
            "status": row[3],
            "started_at": row[4].isoformat() if row[4] else None,
            "completed_at": row[5].isoformat() if row[5] else None,
            "error_message": row[6],
            "stats": row[7] or {},
            "created_at": row[8].isoformat() if row[8] else None,
        }
        for row in rows
    ]

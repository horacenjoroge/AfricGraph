"""Merge history tracking (PostgreSQL) for deduplication and unmerge."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client

TABLE = "merge_history"


def _serialize(v: Any) -> Any:
    if isinstance(v, (datetime,)):
        return v.isoformat()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def ensure_merge_history_table() -> None:
    sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        merged_id VARCHAR(255) NOT NULL,
        survivor_id VARCHAR(255) NOT NULL,
        label VARCHAR(100) NOT NULL,
        merged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        merged_by VARCHAR(50) NOT NULL DEFAULT 'manual',
        confidence FLOAT,
        details JSONB NOT NULL DEFAULT '{{}}',
        undone_at TIMESTAMPTZ,
        undone_by VARCHAR(255)
    );
    CREATE INDEX IF NOT EXISTS idx_merge_history_label_merged_at ON {TABLE}(label, merged_at DESC);
    CREATE INDEX IF NOT EXISTS idx_merge_history_survivor ON {TABLE}(survivor_id);
    CREATE INDEX IF NOT EXISTS idx_merge_history_undone ON {TABLE}(undone_at) WHERE undone_at IS NULL;
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def insert_merge_record(
    merged_id: str,
    survivor_id: str,
    label: str,
    merged_by: str,
    confidence: Optional[float],
    details: Dict[str, Any],
) -> str:
    payload = json.dumps(details, default=_serialize)
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            INSERT INTO {TABLE} (merged_id, survivor_id, label, merged_by, confidence, details)
            VALUES (:merged_id, :survivor_id, :label, :merged_by, :confidence, CAST(:details AS jsonb))
            RETURNING id
            """),
            {"merged_id": merged_id, "survivor_id": survivor_id, "label": label, "merged_by": merged_by, "confidence": confidence, "details": payload},
        )
        (jid,) = r.fetchone()
    return str(jid)


def get_merge_history(
    label: Optional[str] = None,
    merged_id: Optional[str] = None,
    survivor_id: Optional[str] = None,
    undone: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    conditions = ["1=1"]
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if label:
        conditions.append("label = :label")
        params["label"] = label
    if merged_id:
        conditions.append("merged_id = :merged_id")
        params["merged_id"] = merged_id
    if survivor_id:
        conditions.append("survivor_id = :survivor_id")
        params["survivor_id"] = survivor_id
    if undone is False:
        conditions.append("undone_at IS NULL")
    elif undone is True:
        conditions.append("undone_at IS NOT NULL")
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            SELECT id, merged_id, survivor_id, label, merged_at, merged_by, confidence, details, undone_at, undone_by
            FROM {TABLE} WHERE {" AND ".join(conditions)} ORDER BY merged_at DESC LIMIT :limit OFFSET :offset
            """),
            params,
        )
        rows = r.fetchall()
    keys = ["id", "merged_id", "survivor_id", "label", "merged_at", "merged_by", "confidence", "details", "undone_at", "undone_by"]
    return [dict(zip(keys, row)) for row in rows]


def get_merge_record(record_id: str) -> Optional[Dict[str, Any]]:
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"SELECT id, merged_id, survivor_id, label, merged_at, merged_by, confidence, details, undone_at, undone_by FROM {TABLE} WHERE id = :id"),
            {"id": record_id},
        )
        row = r.fetchone()
    if not row:
        return None
    keys = ["id", "merged_id", "survivor_id", "label", "merged_at", "merged_by", "confidence", "details", "undone_at", "undone_by"]
    return dict(zip(keys, row))


def mark_undone(record_id: str, undone_by: Optional[str] = None) -> None:
    with postgres_client.get_session() as s:
        s.execute(
            text(f"UPDATE {TABLE} SET undone_at = now(), undone_by = :ub WHERE id = :id"),
            {"id": record_id, "ub": undone_by or "api"},
        )

"""Workflow state machine and persistence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .models import (
    StepStatus,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowStepState,
)

logger = get_logger(__name__)

DEFINITIONS_TABLE = "workflow_definitions"
INSTANCES_TABLE = "workflow_instances"
HISTORY_TABLE = "workflow_history"


def ensure_tables() -> None:
    """Create workflow tables if they don't exist."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {DEFINITIONS_TABLE} (
        id BIGSERIAL PRIMARY KEY,
        key VARCHAR(100) NOT NULL,
        version INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        definition JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_workflow_definitions_key_version
        ON {DEFINITIONS_TABLE}(key, version);

    CREATE TABLE IF NOT EXISTS {INSTANCES_TABLE} (
        id BIGSERIAL PRIMARY KEY,
        definition_key VARCHAR(100) NOT NULL,
        definition_version INT NOT NULL,
        business_id VARCHAR(255),
        entity_type VARCHAR(100),
        entity_id VARCHAR(255),
        status VARCHAR(50) NOT NULL,
        current_step_index INT NOT NULL DEFAULT 0,
        steps JSONB NOT NULL,
        context JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
        id BIGSERIAL PRIMARY KEY,
        instance_id BIGINT NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        payload JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))


def save_definition(defn: WorkflowDefinition) -> WorkflowDefinition:
    """Persist a workflow definition."""
    ensure_tables()
    payload = defn.model_dump(mode="json")
    with postgres_client.get_session() as s:
        s.execute(
            text(
                f"""
                INSERT INTO {DEFINITIONS_TABLE}
                    (key, version, name, description, definition)
                VALUES
                    (:key, :version, :name, :description, CAST(:definition AS jsonb))
                ON CONFLICT (key, version) DO UPDATE
                SET name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    definition = EXCLUDED.definition
                """
            ),
            {
                "key": defn.key,
                "version": defn.version,
                "name": defn.name,
                "description": defn.description,
                "definition": json.dumps(payload),
            },
        )
    return defn


def get_latest_definition(key: str) -> Optional[WorkflowDefinition]:
    """Fetch latest version of a workflow definition."""
    ensure_tables()
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                SELECT definition
                FROM {DEFINITIONS_TABLE}
                WHERE key = :key
                ORDER BY version DESC
                LIMIT 1
                """
            ),
            {"key": key},
        )
        row = r.fetchone()
    if not row:
        return None
    return WorkflowDefinition.model_validate(row[0])


def _init_instance(defn: WorkflowDefinition, *, business_id: Optional[str], entity_type: Optional[str], entity_id: Optional[str], context: Dict[str, Any]) -> WorkflowInstance:
    steps_state: List[WorkflowStepState] = [
        WorkflowStepState(id=s.id, status=StepStatus.PENDING) for s in defn.steps
    ]
    now = datetime.now(timezone.utc)
    return WorkflowInstance(
        definition_key=defn.key,
        definition_version=defn.version,
        business_id=business_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=WorkflowStatus.PENDING,
        current_step_index=0,
        steps=steps_state,
        context=context or {},
        created_at=now,
        updated_at=now,
    )


def start_workflow(
    key: str,
    *,
    business_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> WorkflowInstance:
    """Create a workflow instance from the latest definition and persist it."""
    defn = get_latest_definition(key)
    if not defn:
        raise ValueError(f"workflow definition not found for key={key}")
    inst = _init_instance(defn, business_id=business_id, entity_type=entity_type, entity_id=entity_id, context=context or {})
    ensure_tables()
    payload_steps = [s.model_dump(mode="json") for s in inst.steps]
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                INSERT INTO {INSTANCES_TABLE}
                  (definition_key, definition_version, business_id, entity_type, entity_id,
                   status, current_step_index, steps, context)
                VALUES
                  (:definition_key, :definition_version, :business_id, :entity_type, :entity_id,
                   :status, :current_step_index, CAST(:steps AS jsonb), CAST(:context AS jsonb))
                RETURNING id, created_at, updated_at
                """
            ),
            {
                "definition_key": inst.definition_key,
                "definition_version": inst.definition_version,
                "business_id": inst.business_id,
                "entity_type": inst.entity_type,
                "entity_id": inst.entity_id,
                "status": inst.status.value,
                "current_step_index": inst.current_step_index,
                "steps": json.dumps(payload_steps),
                "context": json.dumps(inst.context or {}),
            },
        )
        row = r.fetchone()
        inst.id = row[0]
        inst.created_at = row[1]
        inst.updated_at = row[2]
        s.execute(
            text(
                f"""
                INSERT INTO {HISTORY_TABLE} (instance_id, event_type, payload)
                VALUES (:instance_id, :event_type, CAST(:payload AS jsonb))
                """
            ),
            {
                "instance_id": inst.id,
                "event_type": "started",
                "payload": json.dumps({"context": inst.context}),
            },
        )
    return inst


def get_instance(instance_id: int) -> Optional[WorkflowInstance]:
    """Load a workflow instance by id."""
    ensure_tables()
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                SELECT definition_key, definition_version, business_id, entity_type, entity_id,
                       status, current_step_index, steps, context, created_at, updated_at
                FROM {INSTANCES_TABLE}
                WHERE id = :id
                """
            ),
            {"id": instance_id},
        )
        row = r.fetchone()
    if not row:
        return None
    steps_data = row[7]
    steps = [WorkflowStepState.model_validate(x) for x in steps_data]
    return WorkflowInstance(
        id=instance_id,
        definition_key=row[0],
        definition_version=row[1],
        business_id=row[2],
        entity_type=row[3],
        entity_id=row[4],
        status=WorkflowStatus(row[5]),
        current_step_index=row[6],
        steps=steps,
        context=row[8] or {},
        created_at=row[9],
        updated_at=row[10],
    )


def _save_instance(inst: WorkflowInstance, event_type: str, event_payload: Dict[str, Any]) -> None:
    """Persist instance changes and append history event."""
    ensure_tables()
    payload_steps = [s.model_dump(mode="json") for s in inst.steps]
    inst.updated_at = datetime.now(timezone.utc)
    with postgres_client.get_session() as s:
        s.execute(
            text(
                f"""
                UPDATE {INSTANCES_TABLE}
                SET status = :status,
                    current_step_index = :current_step_index,
                    steps = CAST(:steps AS jsonb),
                    context = CAST(:context AS jsonb),
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": inst.id,
                "status": inst.status.value,
                "current_step_index": inst.current_step_index,
                "steps": json.dumps(payload_steps),
                "context": json.dumps(inst.context or {}),
                "updated_at": inst.updated_at,
            },
        )
        s.execute(
            text(
                f"""
                INSERT INTO {HISTORY_TABLE} (instance_id, event_type, payload)
                VALUES (:instance_id, :event_type, CAST(:payload AS jsonb))
                """
            ),
            {
                "instance_id": inst.id,
                "event_type": event_type,
                "payload": json.dumps(event_payload),
            },
        )


def list_history(instance_id: int) -> List[Dict[str, Any]]:
    """Return history events for a workflow instance."""
    ensure_tables()
    with postgres_client.get_session() as s:
        r = s.execute(
            text(
                f"""
                SELECT event_type, payload, created_at
                FROM {HISTORY_TABLE}
                WHERE instance_id = :instance_id
                ORDER BY created_at ASC
                """
            ),
            {"instance_id": instance_id},
        )
        rows = r.fetchall()
    return [
        {"event_type": row[0], "payload": row[1], "created_at": row[2]}
        for row in rows
    ]


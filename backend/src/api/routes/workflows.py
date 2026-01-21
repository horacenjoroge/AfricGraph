"""Workflow engine API endpoints."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.workflows.approval import approve_step, reject_step, request_approval
from src.workflows.engine import (
    ensure_tables,
    get_instance,
    list_history,
    save_definition,
    start_workflow,
)
from src.workflows.models import WorkflowDefinition
from src.workflows.templates import all_templates

router = APIRouter(prefix="/workflows", tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    key: str
    business_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    context: Dict[str, Any] = {}


@router.post("/definitions/install-templates")
def install_templates() -> dict:
    """Install or update pre-built workflow templates."""
    ensure_tables()
    defs = all_templates()
    for d in defs:
        save_definition(d)
    return {"installed": [d.key for d in defs]}


@router.post("/start")
def start_workflow_endpoint(body: StartWorkflowRequest) -> dict:
    """Start a workflow instance from the latest definition."""
    try:
        inst = start_workflow(
            body.key,
            business_id=body.business_id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            context=body.context or {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return inst.model_dump(mode="json")


@router.get("/{instance_id}")
def get_workflow_instance(instance_id: int) -> dict:
    """Get a workflow instance by id."""
    inst = get_instance(instance_id)
    if not inst:
        raise HTTPException(status_code=404, detail="workflow instance not found")
    return inst.model_dump(mode="json")


@router.get("/{instance_id}/history")
def get_workflow_history(instance_id: int) -> dict:
    """Get workflow history events."""
    events = list_history(instance_id)
    return {"items": events}


@router.post("/{instance_id}/request-approval")
def request_approval_endpoint(instance_id: int) -> dict:
    """Move the current step into waiting_approval."""
    inst = request_approval(instance_id)
    return inst.model_dump(mode="json")


class ApprovalBody(BaseModel):
    user_id: str
    reason: Optional[str] = None


@router.post("/{instance_id}/approve")
def approve_step_endpoint(instance_id: int, body: ApprovalBody) -> dict:
    """Approve the current step."""
    inst = approve_step(instance_id, body.user_id)
    return inst.model_dump(mode="json")


@router.post("/{instance_id}/reject")
def reject_step_endpoint(instance_id: int, body: ApprovalBody) -> dict:
    """Reject the current step."""
    inst = reject_step(instance_id, body.user_id, reason=body.reason)
    return inst.model_dump(mode="json")


"""Approval request handling and step transitions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.infrastructure.logging import get_logger
from src.monitoring.instrumentation import track_workflow_approval, record_workflow_approval

from .engine import _save_instance, get_instance
from .models import StepStatus, WorkflowInstance, WorkflowStatus

logger = get_logger(__name__)


def _get_current_step(inst: WorkflowInstance):
    if inst.current_step_index < 0 or inst.current_step_index >= len(inst.steps):
        return None
    return inst.steps[inst.current_step_index]


def request_approval(instance_id: int) -> WorkflowInstance:
    """Mark current step as waiting for approval."""
    inst = get_instance(instance_id)
    if not inst:
        raise ValueError("workflow instance not found")
    step = _get_current_step(inst)
    if not step:
        raise ValueError("no active step")
    if step.status not in (StepStatus.PENDING, StepStatus.WAITING_APPROVAL):
        return inst
    now = datetime.now(timezone.utc)
    step.status = StepStatus.WAITING_APPROVAL
    if not step.started_at:
        step.started_at = now
    if inst.status == WorkflowStatus.PENDING:
        inst.status = WorkflowStatus.RUNNING
    _save_instance(inst, "request_approval", {"step_id": step.id})
    return inst


def approve_step(instance_id: int, user_id: str) -> WorkflowInstance:
    """Approve current step and advance state machine."""
    inst = get_instance(instance_id)
    if not inst:
        raise ValueError("workflow instance not found")
    
    workflow_type = inst.workflow_type or "unknown"
    
    with track_workflow_approval(workflow_type):
        step = _get_current_step(inst)
        if not step:
            raise ValueError("no active step")
        now = datetime.now(timezone.utc)
        step.status = StepStatus.APPROVED
        step.completed_at = now
        step.approved_by = user_id

        # Move to next step or mark workflow approved.
        if inst.current_step_index + 1 < len(inst.steps):
            inst.current_step_index += 1
            next_step = inst.steps[inst.current_step_index]
            next_step.status = StepStatus.PENDING
            inst.status = WorkflowStatus.RUNNING
        else:
            inst.status = WorkflowStatus.APPROVED

        _save_instance(inst, "approved", {"step_id": step.id, "user_id": user_id})
        
        # Record metrics
        record_workflow_approval(workflow_type, "approved")
        
        return inst


def reject_step(instance_id: int, user_id: str, reason: Optional[str] = None) -> WorkflowInstance:
    """Reject current step and mark workflow rejected."""
    inst = get_instance(instance_id)
    if not inst:
        raise ValueError("workflow instance not found")
    
    workflow_type = inst.workflow_type or "unknown"
    
    with track_workflow_approval(workflow_type):
        step = _get_current_step(inst)
        if not step:
            raise ValueError("no active step")
        now = datetime.now(timezone.utc)
        step.status = StepStatus.REJECTED
        step.completed_at = now
        step.rejected_by = user_id
        inst.status = WorkflowStatus.REJECTED
        payload: Dict[str, Any] = {"step_id": step.id, "user_id": user_id}
        if reason:
            payload["reason"] = reason
        _save_instance(inst, "rejected", payload)
        
        # Record metrics
        record_workflow_approval(workflow_type, "rejected")
        
        return inst


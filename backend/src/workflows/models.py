"""Workflow definition and state models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    COMPLETED = "completed"


class Approver(BaseModel):
    """Approver definition: by role or explicit user id."""

    model_config = ConfigDict(extra="forbid")

    user_id: Optional[str] = None
    role: Optional[str] = None


class WorkflowStepDefinition(BaseModel):
    """One step in a workflow definition."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Step id within the workflow")
    name: str
    description: Optional[str] = None
    approvers: List[Approver] = Field(default_factory=list)
    # Simple condition language placeholder: expression evaluated against context.
    condition: Optional[str] = Field(
        default=None,
        description="Optional condition expression (against workflow context) to run this step.",
    )
    timeout_hours: Optional[int] = Field(
        default=None,
        description="Optional SLA/timeout for this step.",
    )
    escalation_role: Optional[str] = Field(
        default=None,
        description="Role to notify if timeout is exceeded.",
    )


class WorkflowDefinition(BaseModel):
    """Workflow template/definition."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., description="Unique workflow key, e.g., supplier_onboarding")
    name: str
    description: Optional[str] = None
    version: int = 1
    steps: List[WorkflowStepDefinition]


class WorkflowStepState(BaseModel):
    """Runtime state for a step."""

    model_config = ConfigDict(extra="forbid")

    id: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowInstance(BaseModel):
    """Workflow runtime instance for a specific business/entity."""

    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    definition_key: str
    definition_version: int
    business_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_index: int = 0
    steps: List[WorkflowStepState] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


"""Pre-built workflow definitions (templates)."""
from __future__ import annotations

from .models import Approver, WorkflowDefinition, WorkflowStepDefinition


def supplier_onboarding_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        key="supplier_onboarding",
        name="Supplier Onboarding Approval",
        description="Multi-step approval for onboarding a new supplier.",
        version=1,
        steps=[
            WorkflowStepDefinition(
                id="compliance_review",
                name="Compliance Review",
                approvers=[Approver(role="compliance")],
            ),
            WorkflowStepDefinition(
                id="finance_review",
                name="Finance Review",
                approvers=[Approver(role="finance")],
            ),
            WorkflowStepDefinition(
                id="executive_approval",
                name="Executive Approval",
                approvers=[Approver(role="executive")],
            ),
        ],
    )


def large_payment_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        key="large_payment",
        name="Large Payment Approval",
        description="Approval workflow for large outgoing payments.",
        version=1,
        steps=[
            WorkflowStepDefinition(
                id="initiator_review",
                name="Initiator Review",
                approvers=[Approver(role="initiator")],
            ),
            WorkflowStepDefinition(
                id="finance_approval",
                name="Finance Approval",
                approvers=[Approver(role="finance")],
            ),
            WorkflowStepDefinition(
                id="cfo_approval",
                name="CFO Approval",
                approvers=[Approver(role="cfo")],
                condition="amount >= 100000",
            ),
        ],
    )


def credit_limit_increase_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        key="credit_limit_increase",
        name="Credit Limit Increase",
        description="Approval workflow for increasing customer credit limits.",
        version=1,
        steps=[
            WorkflowStepDefinition(
                id="risk_review",
                name="Risk Review",
                approvers=[Approver(role="risk")],
            ),
            WorkflowStepDefinition(
                id="sales_lead_approval",
                name="Sales Lead Approval",
                approvers=[Approver(role="sales_lead")],
            ),
        ],
    )


def high_risk_business_review_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        key="high_risk_business_review",
        name="High-Risk Business Review",
        description="Periodic review for high-risk businesses.",
        version=1,
        steps=[
            WorkflowStepDefinition(
                id="risk_team_review",
                name="Risk Team Review",
                approvers=[Approver(role="risk")],
            ),
            WorkflowStepDefinition(
                id="compliance_head_approval",
                name="Compliance Head Approval",
                approvers=[Approver(role="compliance_head")],
            ),
        ],
    )


def all_templates() -> list[WorkflowDefinition]:
    """Return all pre-defined workflow templates."""
    return [
        supplier_onboarding_workflow(),
        large_payment_workflow(),
        credit_limit_increase_workflow(),
        high_risk_business_review_workflow(),
    ]


"""Unit tests for workflow engine."""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.workflows.models import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStatus,
    StepStatus,
)


@pytest.mark.unit
class TestWorkflowModels:
    """Test workflow models."""

    def test_workflow_definition_creation(self):
        """Test creating workflow definition."""
        definition = WorkflowDefinition(
            workflow_type="supplier_onboarding",
            name="Supplier Onboarding",
            steps=[],
        )
        assert definition.workflow_type == "supplier_onboarding"
        assert definition.name == "Supplier Onboarding"

    def test_workflow_instance_creation(self):
        """Test creating workflow instance."""
        instance = WorkflowInstance(
            id=1,
            workflow_type="supplier_onboarding",
            status=WorkflowStatus.PENDING,
            current_step_index=0,
            steps=[],
        )
        assert instance.status == WorkflowStatus.PENDING
        assert instance.current_step_index == 0


@pytest.mark.unit
class TestWorkflowEngine:
    """Test workflow engine."""

    @patch("src.workflows.engine.postgres_client")
    def test_save_definition(self, mock_db):
        """Test saving workflow definition."""
        from src.workflows.engine import save_definition
        
        definition = WorkflowDefinition(
            workflow_type="test_workflow",
            name="Test Workflow",
            steps=[],
        )
        
        result = save_definition(definition)
        assert result is not None
        mock_db.execute.assert_called()

    @patch("src.workflows.engine.postgres_client")
    def test_start_workflow(self, mock_db):
        """Test starting a workflow."""
        from src.workflows.engine import start_workflow
        
        mock_db.fetch_one.return_value = {
            "id": 1,
            "workflow_type": "test_workflow",
            "name": "Test",
            "steps": [],
        }
        
        instance = start_workflow("test_workflow", {"business_id": "123"})
        assert instance is not None
        assert instance.workflow_type == "test_workflow"

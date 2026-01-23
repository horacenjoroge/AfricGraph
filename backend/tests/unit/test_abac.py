"""Unit tests for ABAC."""
import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch

from src.security.abac.attributes import SubjectAttributes, ResourceAttributes, EnvironmentAttributes
from src.security.abac.engine import AbacEngine
from src.security.abac.policies import evaluate_policies, Action


@pytest.mark.unit
@pytest.mark.abac
class TestSubjectAttributes:
    """Test SubjectAttributes."""

    def test_subject_attributes_creation(self):
        """Test creating SubjectAttributes."""
        subject = SubjectAttributes(
            user_id="user-1",
            role="admin",
            business_ids=["business-123"],
            clearance_level=3,
        )
        assert subject.user_id == "user-1"
        assert subject.role == "admin"
        assert "business-123" in subject.business_ids
        assert subject.clearance_level == 3


@pytest.mark.unit
@pytest.mark.abac
class TestResourceAttributes:
    """Test ResourceAttributes."""

    def test_resource_attributes_creation(self):
        """Test creating ResourceAttributes."""
        resource = ResourceAttributes(
            resource_type="Business",
            resource_id="business-123",
            owner_id="owner-1",
            sensitivity_level=0,  # 0 = public
        )
        assert resource.resource_type == "Business"
        assert resource.resource_id == "business-123"
        assert resource.owner_id == "owner-1"
        assert resource.sensitivity_level == 0


@pytest.mark.unit
@pytest.mark.abac
class TestEnvironmentAttributes:
    """Test EnvironmentAttributes."""

    def test_environment_attributes_from_request(self):
        """Test creating EnvironmentAttributes from request."""
        mock_request = Mock()
        mock_request.headers.get.return_value = "192.168.1.1"
        
        env = EnvironmentAttributes.from_request(mock_request)
        assert env.ip_address == "192.168.1.1"
        assert env.hour is not None
        assert env.day_of_week is not None


@pytest.mark.unit
@pytest.mark.abac
class TestABACEngine:
    """Test ABAC engine."""

    def test_admin_authorization(self, admin_subject):
        """Test admin can access everything."""
        engine = AbacEngine()
        resource = ResourceAttributes(resource_type="Business", resource_id="business-123")
        environment = EnvironmentAttributes.default()
        
        decision = engine.authorize(
            action=Action.READ,
            subject=admin_subject,
            resource=resource,
            env=environment,
        )
        assert decision.allowed is True

    def test_owner_authorization_own_business(self, owner_subject):
        """Test owner can access their own business."""
        engine = AbacEngine()
        resource = ResourceAttributes(
            resource_type="Business",
            resource_id="business-123",
            owner_id="owner-1",
        )
        environment = EnvironmentAttributes.default()
        
        decision = engine.authorize(
            action=Action.READ,
            subject=owner_subject,
            resource=resource,
            env=environment,
        )
        assert decision.allowed is True

    def test_owner_authorization_other_business(self, owner_subject):
        """Test owner cannot access other businesses."""
        engine = AbacEngine()
        resource = ResourceAttributes(
            resource_type="Business",
            resource_id="business-456",
            owner_id="owner-2",
        )
        environment = EnvironmentAttributes.default()
        
        decision = engine.authorize(
            action=Action.READ,
            subject=owner_subject,
            resource=resource,
            env=environment,
        )
        assert decision.allowed is False

    def test_analyst_read_access(self, analyst_subject):
        """Test analyst can read non-sensitive data."""
        engine = AbacEngine()
        resource = ResourceAttributes(
            resource_type="Business",
            resource_id="business-123",
            sensitivity_level=0,  # public
        )
        environment = EnvironmentAttributes.default()
        
        decision = engine.authorize(
            action=Action.READ,
            subject=analyst_subject,
            resource=resource,
            env=environment,
        )
        assert decision.allowed is True

    def test_analyst_write_denied(self, analyst_subject):
        """Test analyst cannot write."""
        engine = AbacEngine()
        resource = ResourceAttributes(resource_type="Business", resource_id="business-123")
        environment = EnvironmentAttributes.default()
        
        decision = engine.authorize(
            action=Action.WRITE,
            subject=analyst_subject,
            resource=resource,
            env=environment,
        )
        assert decision.allowed is False

    def test_time_based_restriction(self, admin_subject):
        """Test time-based access restrictions."""
        engine = AbacEngine()
        resource = ResourceAttributes(resource_type="Business", resource_id="business-123")
        
        # Outside business hours
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("UTC")).replace(hour=22, minute=0)
        env = EnvironmentAttributes(
            ip_address="",
            timezone="UTC",
            hour=now.hour,
            day_of_week=now.weekday(),
        )
        
        decision = engine.authorize(
            action=Action.WRITE,
            subject=admin_subject,
            resource=resource,
            env=env,
        )
        # Should still allow (admin override) but log restriction
        assert decision.allowed is True

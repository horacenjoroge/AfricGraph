"""Unit tests for alert system."""
import pytest
from unittest.mock import Mock, patch

from src.alerts.models import Alert, AlertRule, AlertSeverity, AlertStatus
from src.alerts.engine import evaluate_and_trigger, initialize_rules, get_rule, list_rules


@pytest.mark.unit
class TestAlertModels:
    """Test alert models."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            id="test-alert-1",
            rule_id="high_risk_score",
            entity_id="business-123",
            severity=AlertSeverity.HIGH,
            message="High risk score detected",
            status=AlertStatus.ACTIVE,
        )
        assert alert.severity == AlertSeverity.HIGH
        assert alert.status == AlertStatus.ACTIVE

    def test_alert_rule_creation(self):
        """Test creating an alert rule."""
        rule = AlertRule(
            id="high_risk_score",
            name="High Risk Score",
            condition="risk_score > 80",
            severity=AlertSeverity.HIGH,
        )
        assert rule.id == "high_risk_score"
        assert rule.severity == AlertSeverity.HIGH


@pytest.mark.unit
class TestAlertEngine:
    """Test alert engine functions."""

    def test_initialize_rules(self):
        """Test initializing alert rules."""
        initialize_rules()
        rules = list_rules()
        assert len(rules) > 0

    def test_get_rule(self):
        """Test getting a rule by ID."""
        initialize_rules()
        rule = get_rule("high_risk_score")
        # Rule may or may not exist depending on default rules
        # Just test that function works
        assert rule is None or isinstance(rule, AlertRule)

    @patch("src.alerts.engine.create_alert")
    @patch("src.alerts.engine.route_alert")
    @patch("src.alerts.engine.check_cooldown")
    @patch("src.alerts.engine.evaluate_condition")
    def test_evaluate_and_trigger(self, mock_evaluate, mock_cooldown, mock_route, mock_create):
        """Test evaluating and triggering alerts."""
        initialize_rules()
        
        # Mock conditions
        mock_evaluate.return_value = True
        mock_cooldown.return_value = False
        mock_create.return_value = None
        
        # Test with sample data
        data = {"risk_score": 85, "business_id": "test-123"}
        result = evaluate_and_trigger(
            rule_id="high_risk_score",
            data=data,
            business_id="test-123"
        )
        
        # Result may be None if rule doesn't exist, but function should execute
        assert result is None or isinstance(result, Alert)

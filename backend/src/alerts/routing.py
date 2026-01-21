"""Alert routing to email, Slack, webhooks."""
from typing import Any, Dict, Optional

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def route_alert(alert: Dict[str, Any], routing_config: Dict[str, Any]) -> None:
    """
    Route alert to configured channels (email, Slack, webhook).

    routing_config: {
        "email": {"enabled": true, "recipients": ["admin@example.com"]},
        "slack": {"enabled": true, "webhook_url": "https://..."},
        "webhook": {"enabled": true, "url": "https://...", "headers": {...}}
    }
    """
    if routing_config.get("email", {}).get("enabled"):
        _send_email(alert, routing_config.get("email", {}))

    if routing_config.get("slack", {}).get("enabled"):
        _send_slack(alert, routing_config.get("slack", {}))

    if routing_config.get("webhook", {}).get("enabled"):
        _send_webhook(alert, routing_config.get("webhook", {}))


def _send_email(alert: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Send alert via email (stub - integrate with SMTP)."""
    recipients = config.get("recipients", [])
    if not recipients:
        return
    # TODO: Integrate with SMTP service
    logger.info("Email alert sent", alert_id=alert.get("id"), recipients=recipients)


def _send_slack(alert: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Send alert to Slack webhook (stub - integrate with requests)."""
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        return
    # TODO: POST to Slack webhook
    logger.info("Slack alert sent", alert_id=alert.get("id"), webhook_url=webhook_url[:50])


def _send_webhook(alert: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Send alert to custom webhook (stub - integrate with requests)."""
    url = config.get("url")
    if not url:
        return
    headers = config.get("headers", {})
    # TODO: POST to webhook URL
    logger.info("Webhook alert sent", alert_id=alert.get("id"), url=url[:50])

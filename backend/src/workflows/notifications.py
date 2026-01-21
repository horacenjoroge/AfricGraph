"""Notification stubs for workflows (email/SMS/Slack hooks)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def notify_approver(channel: str, target: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Stub for sending notifications.

    channel: "email" | "sms" | "slack" | etc.
    target: address / phone / channel id.
    """
    logger.info(
        "workflow_notification",
        channel=channel,
        target=target,
        message=message,
        extra=extra or {},
    )


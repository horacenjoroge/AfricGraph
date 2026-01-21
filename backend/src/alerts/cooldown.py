"""Alert cooldown logic to prevent spam."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client


def check_cooldown(
    rule_id: str,
    business_id: Optional[str],
    entity_id: Optional[str],
    cooldown_minutes: int,
) -> bool:
    """
    Check if alert is in cooldown period.

    Returns True if alert should be suppressed (in cooldown), False if it can fire.
    """
    if cooldown_minutes <= 0:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)

    # Check for recent alert of same rule for same entity
    conditions = ["rule_id = :rule_id", "created_at > :cutoff", "status != 'dismissed'"]
    params = {"rule_id": rule_id, "cutoff": cutoff}

    if business_id:
        conditions.append("business_id = :business_id")
        params["business_id"] = business_id
    if entity_id:
        conditions.append("entity_id = :entity_id")
        params["entity_id"] = entity_id

    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            SELECT COUNT(*) FROM alerts
            WHERE {' AND '.join(conditions)}
            """),
            params,
        )
        count = r.fetchone()[0]

    return count > 0

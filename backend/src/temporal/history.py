"""Change history tracking and visualization."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.temporal.models import ChangeHistory

logger = get_logger(__name__)


class ChangeHistoryManager:
    """Manages change history for visualization and auditing."""

    def get_entity_history(
        self,
        entity_id: str,
        entity_type: str = "node",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ChangeHistory]:
        """
        Get change history for an entity.

        Args:
            entity_id: Entity identifier
            entity_type: Entity type ("node" or "relationship")
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of change history entries
        """
        conditions = [
            "entity_id = %(entity_id)s",
            "entity_type = %(entity_type)s",
        ]
        params = {
            "entity_id": entity_id,
            "entity_type": entity_type,
        }

        if start_time:
            conditions.append("timestamp >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("timestamp <= %(end_time)s")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT change_id, entity_id, entity_type, change_type, timestamp, version,
               old_properties, new_properties, changed_by
        FROM change_history
        WHERE {where_clause}
        ORDER BY timestamp ASC
        """
        
        with postgres_client.get_session() as session:
            result = session.execute(text(query), params)
            rows = [dict(row) for row in result]
        
        return [
            ChangeHistory(
                change_id=row["change_id"],
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                change_type=row["change_type"],
                timestamp=row["timestamp"],
                version=row["version"],
                old_properties=row.get("old_properties"),
                new_properties=row.get("new_properties"),
                changed_by=row.get("changed_by"),
            )
            for row in rows
        ]

    def get_changes_in_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        entity_type: Optional[str] = None,
        change_type: Optional[str] = None,
    ) -> List[ChangeHistory]:
        """
        Get all changes in a time frame.

        Args:
            start_time: Start of time frame
            end_time: End of time frame
            entity_type: Optional entity type filter
            change_type: Optional change type filter

        Returns:
            List of change history entries
        """
        conditions = [
            "timestamp >= %(start_time)s",
            "timestamp <= %(end_time)s",
        ]
        params = {
            "start_time": start_time,
            "end_time": end_time,
        }

        if entity_type:
            conditions.append("entity_type = %(entity_type)s")
            params["entity_type"] = entity_type

        if change_type:
            conditions.append("change_type = %(change_type)s")
            params["change_type"] = change_type

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT change_id, entity_id, entity_type, change_type, timestamp, version,
               old_properties, new_properties, changed_by
        FROM change_history
        WHERE {where_clause}
        ORDER BY timestamp ASC
        """
        
        with postgres_client.get_session() as session:
            result = session.execute(text(query), params)
            rows = [dict(row) for row in result]
        
        return [
            ChangeHistory(
                change_id=row["change_id"],
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                change_type=row["change_type"],
                timestamp=row["timestamp"],
                version=row["version"],
                old_properties=row.get("old_properties"),
                new_properties=row.get("new_properties"),
                changed_by=row.get("changed_by"),
            )
            for row in rows
        ]

    def get_change_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get summary of changes.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary with change statistics
        """
        conditions = ["1=1"]
        params = {}

        if start_time:
            conditions.append("timestamp >= %(start_time)s")
            params["start_time"] = start_time

        if end_time:
            conditions.append("timestamp <= %(end_time)s")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT 
            entity_type,
            change_type,
            COUNT(*) as count
        FROM change_history
        WHERE {where_clause}
        GROUP BY entity_type, change_type
        ORDER BY entity_type, change_type
        """
        
        with postgres_client.get_session() as session:
            result = session.execute(text(query), params)
            rows = [dict(row) for row in result]
        
        summary = {
            "total_changes": sum(row["count"] for row in rows),
            "by_entity_type": {},
            "by_change_type": {},
        }
        
        for row in rows:
            entity_type = row["entity_type"]
            change_type = row["change_type"]
            count = row["count"]
            
            if entity_type not in summary["by_entity_type"]:
                summary["by_entity_type"][entity_type] = {}
            summary["by_entity_type"][entity_type][change_type] = count
            
            if change_type not in summary["by_change_type"]:
                summary["by_change_type"][change_type] = 0
            summary["by_change_type"][change_type] += count
        
        return summary

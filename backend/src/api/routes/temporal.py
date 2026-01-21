"""Temporal and time-travel query API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.temporal.queries import TemporalQueryEngine
from src.temporal.snapshots import SnapshotManager
from src.temporal.history import ChangeHistoryManager
from src.temporal.restore import RestoreManager
from src.infrastructure.logging import get_logger

router = APIRouter(prefix="/temporal", tags=["temporal"])
logger = get_logger(__name__)

query_engine = TemporalQueryEngine()
snapshot_manager = SnapshotManager()
history_manager = ChangeHistoryManager()
restore_manager = RestoreManager()


class TemporalQueryRequest(BaseModel):
    """Temporal query request."""
    timestamp: datetime
    node_ids: Optional[List[str]] = None
    relationship_ids: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    rel_types: Optional[List[str]] = None


class SnapshotCreateRequest(BaseModel):
    """Snapshot creation request."""
    timestamp: Optional[datetime] = None
    description: Optional[str] = None


class RestoreRequest(BaseModel):
    """Restore request."""
    timestamp: Optional[datetime] = None
    snapshot_id: Optional[str] = None
    node_ids: Optional[List[str]] = None
    relationship_ids: Optional[List[str]] = None
    dry_run: bool = False


@router.post("/query")
def query_at_time(request: TemporalQueryRequest) -> dict:
    """
    Query graph state at a specific point in time.

    Returns nodes and relationships valid at the specified timestamp.
    """
    try:
        result = query_engine.query_at_time(
            timestamp=request.timestamp,
            node_ids=request.node_ids,
            relationship_ids=request.relationship_ids,
            labels=request.labels,
            rel_types=request.rel_types,
        )
        return {
            "timestamp": result.timestamp.isoformat(),
            "nodes": [node.model_dump(mode="json") for node in result.nodes],
            "relationships": [rel.model_dump(mode="json") for rel in result.relationships],
            "total_nodes": result.total_nodes,
            "total_relationships": result.total_relationships,
        }
    except Exception as e:
        logger.exception("Temporal query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/node/{node_id}/history")
def get_node_history(
    node_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
) -> dict:
    """Get version history for a node."""
    try:
        history = history_manager.get_entity_history(
            entity_id=node_id,
            entity_type="node",
            start_time=start_time,
            end_time=end_time,
        )
        return {
            "node_id": node_id,
            "history": [change.model_dump(mode="json") for change in history],
        }
    except Exception as e:
        logger.exception("Failed to get node history", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/relationship/{relationship_id}/history")
def get_relationship_history(
    relationship_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
) -> dict:
    """Get version history for a relationship."""
    try:
        history = history_manager.get_entity_history(
            entity_id=relationship_id,
            entity_type="relationship",
            start_time=start_time,
            end_time=end_time,
        )
        return {
            "relationship_id": relationship_id,
            "history": [change.model_dump(mode="json") for change in history],
        }
    except Exception as e:
        logger.exception("Failed to get relationship history", relationship_id=relationship_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.post("/snapshots")
def create_snapshot(request: SnapshotCreateRequest) -> dict:
    """Create a graph snapshot at a point in time."""
    try:
        snapshot = snapshot_manager.create_snapshot(
            timestamp=request.timestamp,
            description=request.description,
        )
        return snapshot.model_dump(mode="json")
    except Exception as e:
        logger.exception("Failed to create snapshot", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/snapshots")
def list_snapshots(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """List graph snapshots."""
    try:
        snapshots = snapshot_manager.list_snapshots(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return {
            "snapshots": [snapshot.model_dump(mode="json") for snapshot in snapshots],
            "total": len(snapshots),
        }
    except Exception as e:
        logger.exception("Failed to list snapshots", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: str) -> dict:
    """Get snapshot by ID."""
    snapshot = snapshot_manager.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot.model_dump(mode="json")


@router.post("/restore")
def restore_graph(request: RestoreRequest) -> dict:
    """
    Restore graph to a previous state.

    Can restore from timestamp or snapshot.
    """
    try:
        if request.snapshot_id:
            result = restore_manager.restore_from_snapshot(
                snapshot_id=request.snapshot_id,
                dry_run=request.dry_run,
            )
        elif request.timestamp:
            result = restore_manager.restore_to_timestamp(
                timestamp=request.timestamp,
                node_ids=request.node_ids,
                relationship_ids=request.relationship_ids,
                dry_run=request.dry_run,
            )
        else:
            raise HTTPException(status_code=400, detail="Must provide either timestamp or snapshot_id")
        
        return result
    except Exception as e:
        logger.exception("Restore failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.get("/changes")
def get_changes(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    entity_type: Optional[str] = Query(None),
    change_type: Optional[str] = Query(None),
) -> dict:
    """Get change history in a time frame."""
    try:
        changes = history_manager.get_changes_in_timeframe(
            start_time=start_time or datetime.min,
            end_time=end_time or datetime.now(),
            entity_type=entity_type,
            change_type=change_type,
        )
        return {
            "changes": [change.model_dump(mode="json") for change in changes],
            "total": len(changes),
        }
    except Exception as e:
        logger.exception("Failed to get changes", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")


@router.get("/changes/summary")
def get_change_summary(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
) -> dict:
    """Get summary of changes."""
    try:
        summary = history_manager.get_change_summary(
            start_time=start_time,
            end_time=end_time,
        )
        return summary
    except Exception as e:
        logger.exception("Failed to get change summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

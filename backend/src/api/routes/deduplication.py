"""Deduplication: candidates, merge, auto-merge, merge history, unmerge."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.deduplication.candidates import find_candidates
from src.deduplication.merge import merge_nodes, unmerge
from src.deduplication.merge_history import get_merge_history, get_merge_record, insert_merge_record, mark_undone
from src.infrastructure.database.neo4j_client import neo4j_client

router = APIRouter(prefix="/deduplication", tags=["deduplication"])


class MergeBody(BaseModel):
    merged_id: str = Field(..., description="Node id to remove (merge into survivor)")
    survivor_id: str = Field(..., description="Node id to keep")
    label: str = Field(..., description="Node label")
    confidence: Optional[float] = None
    auto_approved: bool = Field(False, description="If true and confidence >= threshold, merged_by=auto")


class AutoMergeBody(BaseModel):
    label: str = Field(..., description="Node label")
    min_confidence: float = Field(0.95, description="Only merge candidates >= this")


class UnmergeBody(BaseModel):
    merge_history_id: str = Field(..., description="Record to undo")


@router.get("/candidates")
def get_candidates(
    label: str,
    min_confidence: float = 0.8,
    limit: int = 100,
) -> dict:
    """Return merge candidates: pairs of nodes with similarity >= min_confidence."""
    try:
        cands = find_candidates(neo4j_client, label, min_confidence=min_confidence, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"candidates": cands}


@router.post("/merge")
def post_merge(body: MergeBody) -> dict:
    """Merge merged_id into survivor_id. Manual by default; auto if auto_approved and confidence >= threshold."""
    thr = getattr(settings, "deduplication_auto_merge_confidence_threshold", 0.95)
    merged_by = "auto" if (body.auto_approved and (body.confidence or 0) >= thr) else "manual"
    try:
        details = merge_nodes(neo4j_client, body.merged_id, body.survivor_id, body.label, merged_by=merged_by, confidence=body.confidence)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    rid = insert_merge_record(body.merged_id, body.survivor_id, body.label, merged_by, body.confidence, details)
    return {"merge_history_id": rid, "merged_id": body.merged_id, "survivor_id": body.survivor_id, "merged_by": merged_by}


@router.post("/auto-merge")
def post_auto_merge(body: AutoMergeBody) -> dict:
    """Find candidates >= min_confidence and merge them (merged_by=auto)."""
    try:
        cands = find_candidates(neo4j_client, body.label, min_confidence=body.min_confidence, limit=getattr(settings, "deduplication_candidates_limit", 500))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    merged = []
    for c in cands:
        a, b = c["node_a_id"], c["node_b_id"]
        conf = c.get("confidence") or 0
        try:
            details = merge_nodes(neo4j_client, a, b, body.label, merged_by="auto", confidence=conf)
            rid = insert_merge_record(a, b, body.label, "auto", conf, details)
            merged.append({"merge_history_id": rid, "merged_id": a, "survivor_id": b})
        except Exception:
            continue
    return {"merged": merged}


@router.get("/merge-history")
def get_history(
    label: Optional[str] = None,
    merged_id: Optional[str] = None,
    survivor_id: Optional[str] = None,
    undone: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Query merge history. undone=false: only active; undone=true: only undone."""
    items = get_merge_history(label=label, merged_id=merged_id, survivor_id=survivor_id, undone=undone, limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset}


@router.post("/unmerge")
def post_unmerge(body: UnmergeBody) -> dict:
    """Recreate merged node and its relationships, remove moved rels from survivor, mark record undone."""
    try:
        unmerge(neo4j_client, body.merge_history_id, get_merge_record, mark_undone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    rec = get_merge_record(body.merge_history_id)
    return {"merge_history_id": body.merge_history_id, "undone_at": rec.get("undone_at") if rec else None}

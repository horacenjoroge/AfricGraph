"""Merge and unmerge: move relationships (with merged_from_id), delete merged node, history."""
import json
from typing import Any, Dict, List, Optional

from src.domain.ontology import NODE_LABELS, RELATIONSHIP_TYPES


def _props_to_dict(p: Any) -> Dict[str, Any]:
    if p is None:
        return {}
    if isinstance(p, dict):
        return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in p.items()}
    return {}


def merge_nodes(
    neo4j_client,
    merged_id: str,
    survivor_id: str,
    label: str,
    merged_by: str = "manual",
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    In one write_transaction: move (a)-[r]-(x) to (survivor)-[r']-(x) with r'.merged_from_id=merged_id,
    then DETACH DELETE (a). Returns details for merge_history: {merged_props, moved_relationships}.
    """
    if label not in NODE_LABELS:
        raise ValueError(f"Invalid label: {label}")
    if merged_id == survivor_id:
        raise ValueError("merged_id and survivor_id must differ")

    def _tx(tx):
        # 1) properties of merged node
        r0 = tx.run(f"MATCH (a:{label} {{id: $mid}}) RETURN properties(a) AS props", {"mid": merged_id})
        rec0 = r0.single()
        if not rec0:
            raise ValueError(f"Node not found: {label} {{id: {merged_id!r}}}")
        merged_props = _props_to_dict(rec0["props"])
        if "id" not in merged_props:
            merged_props["id"] = merged_id

        # 2) all (a)-[r]-(x)
        r1 = tx.run(
            f"MATCH (a:{label} {{id: $mid}})-[r]-(x) RETURN id(r) AS rid, type(r) AS rel_type, properties(r) AS props, startNode(r).id AS start_id, endNode(r).id AS end_id",
            {"mid": merged_id},
        )
        rels = []
        for rec in r1:
            rid = rec["rid"]
            rt = rec["rel_type"]
            if rt not in RELATIONSHIP_TYPES:
                continue
            start_id = rec["start_id"]
            end_id = rec["end_id"]
            if start_id is None or end_id is None:
                continue
            start_id = str(start_id)
            end_id = str(end_id)
            p = _props_to_dict(rec["props"])
            rels.append({"rid": rid, "rel_type": rt, "props": p, "start_id": start_id, "end_id": end_id})

        moved = []
        for r in rels:
            # new endpoints: replace merged_id with survivor_id
            new_start = survivor_id if r["start_id"] == merged_id else r["start_id"]
            new_end = survivor_id if r["end_id"] == merged_id else r["end_id"]
            on_create = {**r["props"], "merged_from_id": merged_id}
            tx.run(
                "MATCH (fn {id: $from_id}), (tn {id: $to_id}) CALL apoc.merge.relationship(fn, $rel_type, {}, tn, $on_create, {}) YIELD rel RETURN 1",
                {"from_id": new_start, "to_id": new_end, "rel_type": r["rel_type"], "on_create": on_create},
            )
            tx.run("MATCH ()-[r]-() WHERE id(r) = $rid DELETE r", {"rid": r["rid"]})
            moved.append({"from_id": r["start_id"], "to_id": r["end_id"], "type": r["rel_type"], "props": r["props"]})

        tx.run(f"MATCH (a:{label} {{id: $mid}}) DETACH DELETE a", {"mid": merged_id})

        return {"merged_props": merged_props, "moved_relationships": moved}

    details = neo4j_client.write_transaction(_tx)
    return details


def unmerge(
    neo4j_client,
    merge_history_id: str,
    get_merge_record,
    mark_undone_fn,
) -> None:
    """
    Recreate merged node and its relationships, delete rels with merged_from_id on survivor, mark record undone.
    """
    rec = get_merge_record(merge_history_id)
    if not rec:
        raise ValueError("merge history record not found")
    if rec.get("undone_at") is not None:
        raise ValueError("merge already undone")
    merged_id = rec["merged_id"]
    survivor_id = rec["survivor_id"]
    label = rec["label"]
    details = rec.get("details") or {}
    if isinstance(details, str):
        details = json.loads(details) if details else {}
    merged_props = details.get("merged_props") or {}
    moved = details.get("moved_relationships") or []
    if "id" not in merged_props:
        merged_props = dict(merged_props, id=merged_id)

    if label not in NODE_LABELS:
        raise ValueError(f"Invalid label in record: {label}")

    def _tx(tx):
        # 1) CREATE (n:Label $props)
        tx.run(f"CREATE (n:{label}) SET n = $props", {"props": merged_props})
        # 2) CREATE each original relationship (from_id)-[type]-(to_id)
        for m in moved:
            t = m.get("type") or ""
            if t not in RELATIONSHIP_TYPES:
                continue
            tx.run(
                f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) CREATE (a)-[r:{t}]->(b) SET r = $props",
                {"from_id": m["from_id"], "to_id": m["to_id"], "props": m.get("props") or {}},
            )
        # 3) DELETE (other)-[r:type]-(survivor) WHERE r.merged_from_id = merged_id
        for m in moved:
            t = m.get("type") or ""
            if t not in RELATIONSHIP_TYPES:
                continue
            other = m["to_id"] if m["from_id"] == merged_id else m["from_id"]
            tx.run(
                f"MATCH (o {{id: $oid}})-[r:{t}]-(s {{id: $sid}}) WHERE r.merged_from_id = $mid DELETE r",
                {"oid": other, "sid": survivor_id, "mid": merged_id},
            )

    neo4j_client.write_transaction(_tx)
    mark_undone_fn(merge_history_id, "api")

"""Merge candidates: fetch nodes from Neo4j, block, pairwise composite similarity."""
from typing import Any, Dict, List, Optional

from src.domain.ontology import NODE_LABELS

from .detection import composite_similarity


def find_candidates(
    neo4j_client,
    label: str,
    min_confidence: float = 0.8,
    limit: int = 100,
    block_size: int = 1,
) -> List[Dict[str, Any]]:
    """
    Returns [{node_a_id, node_b_id, confidence, reasons}]. Uses blocking on first N chars of name.
    block_size=0 disables blocking (full N^2).
    """
    if label not in NODE_LABELS:
        raise ValueError(f"Invalid label: {label}. Must be in {NODE_LABELS}")
    query = f"MATCH (n:{label}) RETURN n.id AS id, n.name AS name, n.phone AS phone, n.address AS address"
    rows = neo4j_client.execute_cypher(query)
    nodes = []
    for r in rows:
        nid = r.get("id")
        if not nid:
            continue
        nodes.append({
            "id": str(nid),
            "name": r.get("name"),
            "phone": r.get("phone"),
            "address": r.get("address"),
        })
    if len(nodes) < 2:
        return []

    if block_size and block_size > 0:
        blocks: Dict[str, List[Dict]] = {}
        for n in nodes:
            k = (n.get("name") or n.get("id") or "").strip().lower()[:block_size] or "_"
            blocks.setdefault(k, []).append(n)
        pairs: List[tuple] = []
        for grp in blocks.values():
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    pairs.append((grp[i], grp[j]))
    else:
        pairs = [(nodes[i], nodes[j]) for i in range(len(nodes)) for j in range(i + 1, len(nodes))]

    out: List[Dict[str, Any]] = []
    for a, b in pairs:
        score, reasons = composite_similarity(
            a.get("name"), b.get("name"),
            a.get("phone"), b.get("phone"),
            a.get("address"), b.get("address"),
        )
        if score >= min_confidence:
            out.append({"node_a_id": a["id"], "node_b_id": b["id"], "confidence": score, "reasons": reasons})
    out.sort(key=lambda x: -x["confidence"])
    return out[:limit]

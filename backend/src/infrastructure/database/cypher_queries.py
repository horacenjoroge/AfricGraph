"""
Reusable Cypher query templates with parameterization.

Label and relationship-type placeholders are filled only after
allowlist validation (ontology) to prevent injection.
"""

from typing import Dict, List, Any, Optional

from src.domain.ontology import NODE_LABELS, RELATIONSHIP_TYPES


def _check_label(label: str) -> None:
    if label not in NODE_LABELS:
        raise ValueError(f"Invalid node label: {label}")


def _check_rel_type(rel_type: str) -> None:
    if rel_type not in RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship type: {rel_type}")


def _check_identifiers(keys: List[str]) -> None:
    import re
    pat = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    for k in keys:
        if not pat.match(k):
            raise ValueError(f"Invalid property or filter key: {k}")


# ---------------------------------------------------------------------------
# Node CRUD
# ---------------------------------------------------------------------------


def create_node_query(label: str) -> str:
    """Return CREATE (n:Label) SET n = $properties RETURN id(n) as node_id. Label must be in NODE_LABELS."""
    _check_label(label)
    return f"CREATE (n:{label}) SET n = $properties RETURN id(n) as node_id"


def find_node_query(label: str, filter_keys: List[str]) -> str:
    """Return MATCH (n:Label) WHERE <key=param> RETURN n LIMIT 1. filter_keys must be valid identifiers."""
    _check_label(label)
    _check_identifiers(filter_keys)
    if not filter_keys:
        return f"MATCH (n:{label}) RETURN n LIMIT 1"
    where = " AND ".join(f"n.{k} = ${k}" for k in filter_keys)
    return f"MATCH (n:{label}) WHERE {where} RETURN n LIMIT 1"


def create_relationship_query(rel_type: str) -> str:
    """Return MATCH (a),(b) WHERE id(a)=$from_id AND id(b)=$to_id CREATE (a)-[r:Type $props]->(b) RETURN r."""
    _check_rel_type(rel_type)
    return (
        "MATCH (a), (b) WHERE id(a) = $from_id AND id(b) = $to_id "
        f"CREATE (a)-[r:{rel_type} $props]->(b) RETURN r"
    )


# ---------------------------------------------------------------------------
# Traversal and path
# ---------------------------------------------------------------------------


def traverse_query(rel_types: Optional[List[str]], max_depth: int) -> str:
    """Return variable-depth traversal from start. rel_types: optional list of types to follow (all if None)."""
    for r in (rel_types or []):
        _check_rel_type(r)
    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")
    # Variable-length: [rls*1..max] or [rls:T1|T2*1..max]. rls is the list of rels.
    rel_pattern = "rls*1.." + str(max_depth)
    if rel_types:
        types_part = "|".join(rel_types)
        rel_pattern = "rls:" + types_part + "*1.." + str(max_depth)
    return (
        "MATCH (start) WHERE id(start) = $start_id "
        f"MATCH path = (start)-[{rel_pattern}]->(n) "
        "WITH start, collect(DISTINCT n) as nodes, relationships(path) as rlist "
        "UNWIND rlist as r "
        "WITH start, nodes, collect(DISTINCT r) as rel_list "
        "RETURN id(start) as start_id, "
        "[x in nodes | {id: id(x), labels: labels(x), props: properties(x)}] as nodes, "
        "[x in rel_list | {type: type(x), from: id(startNode(x)), to: id(endNode(x)), props: properties(x)}] as relationships"
    )


def find_path_query(max_depth: int) -> str:
    """Return shortest path(s) between start and end. Uses shortestPath."""
    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")
    return (
        "MATCH (a), (b) WHERE id(a) = $start_id AND id(b) = $end_id "
        f"MATCH path = shortestPath((a)-[*1..{max_depth}]->(b)) "
        "RETURN [n in nodes(path) | {id: id(n), labels: labels(n), props: properties(n)}] as nodes, "
        "[r in relationships(path) | {type: type(r), from: id(startNode(r)), to: id(endNode(r)), props: properties(r)}] as rels"
    )


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


def batch_create_nodes_query() -> str:
    """UNWIND $nodes as row; each row is {label, props}. Uses apoc.create.node. Caller must validate label in NODE_LABELS."""
    return (
        "UNWIND $nodes as row "
        "CALL apoc.create.node([row.label], row.props) YIELD node "
        "RETURN collect(id(node)) as ids"
    )


def batch_create_relationships_query() -> str:
    """UNWIND $rels as r MATCH (a), (b) WHERE id(a)=r.from_id AND id(b)=r.to_id CREATE (a)-[r:Type $r.props]->(b).
    Relationship type varies per row. We need to create different types. Without dynamic type we'd need one UNWIND per type
    or apoc. apoc.create.relationship(a, type, props, b) = apoc.create.relationship(startNode, relType, props, endNode).
    UNWIND $rels as row
    MATCH (a), (b) WHERE id(a) = row.from_id AND id(b) = row.to_id
    CALL apoc.create.relationship(a, row.type, coalesce(row.props, {}), b) YIELD rel
    RETURN count(rel) as count
    """
    return (
        "UNWIND $rels as row "
        "MATCH (a), (b) WHERE id(a) = row.from_id AND id(b) = row.to_id "
        "CALL apoc.create.relationship(a, row.type, coalesce(row.props, {}), b) YIELD rel "
        "RETURN count(rel) as count"
    )


# ---------------------------------------------------------------------------
# Upsert (MERGE) for idempotent ingestion
# ---------------------------------------------------------------------------


def merge_node_query(label: str) -> str:
    """MERGE (n:Label {id: $id, tenant_id: $tenant_id}) ON CREATE SET n = $props ON MATCH SET n = $props RETURN id(n) as node_id.
    props must include id and tenant_id. Label must be in NODE_LABELS.
    CRITICAL: tenant_id is included in MERGE to ensure tenant isolation - same ID in different tenants creates separate nodes."""
    _check_label(label)
    return f"MERGE (n:{label} {{id: $id, tenant_id: $tenant_id}}) ON CREATE SET n = $props ON MATCH SET n = $props RETURN id(n) as node_id"


def merge_relationship_by_business_id_query(from_label: str, to_label: str, rel_type: str) -> str:
    """MATCH (a:FromLabel {id: $from_id, tenant_id: $tenant_id}), (b:ToLabel {id: $to_id, tenant_id: $tenant_id}) MERGE (a)-[r:RelType]->(b) SET r += $props.
    Uses business id (string), not internal neo4j id.
    CRITICAL: tenant_id is included in MATCH to ensure tenant isolation."""
    _check_label(from_label)
    _check_label(to_label)
    _check_rel_type(rel_type)
    return (
        f"MATCH (a:{from_label} {{id: $from_id, tenant_id: $tenant_id}}), (b:{to_label} {{id: $to_id, tenant_id: $tenant_id}}) "
        f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
    )



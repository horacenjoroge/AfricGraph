"""Graph metrics: centrality, PageRank."""
from typing import List, Optional

from src.infrastructure.database.neo4j_client import neo4j_client

from .models import GraphMetrics


def compute_node_metrics(node_id: str, include_centrality: bool = True) -> GraphMetrics:
    """
    Compute graph metrics for a node: degree, centrality, PageRank.

    Uses APOC procedures for centrality calculations.
    """
    # Basic degree
    query = """
    MATCH (n) WHERE id(n) = $node_id
    OPTIONAL MATCH (n)-[r1]->()
    OPTIONAL MATCH ()-[r2]->(n)
    RETURN 
        count(DISTINCT r1) as out_degree,
        count(DISTINCT r2) as in_degree,
        count(DISTINCT r1) + count(DISTINCT r2) as degree
    """
    rows = neo4j_client.execute_cypher(query, {"node_id": int(node_id)})
    if not rows:
        return GraphMetrics(node_id=node_id)

    row = rows[0]
    degree = row.get("degree", 0)
    in_degree = row.get("in_degree", 0)
    out_degree = row.get("out_degree", 0)

    metrics = GraphMetrics(
        node_id=node_id, degree=degree, in_degree=in_degree, out_degree=out_degree
    )

    if include_centrality:
        # Betweenness centrality (APOC)
        try:
            bc_query = """
            MATCH (n) WHERE id(n) = $node_id
            CALL apoc.algo.betweenness(['*'], ['*'], 'BOTH') YIELD node, score
            WHERE id(node) = $node_id
            RETURN score as betweenness
            """
            bc_rows = neo4j_client.execute_cypher(bc_query, {"node_id": int(node_id)})
            if bc_rows and bc_rows[0].get("betweenness") is not None:
                metrics.betweenness_centrality = float(bc_rows[0]["betweenness"])
        except Exception:
            pass  # APOC may not be available or may fail

        # PageRank (APOC)
        try:
            pr_query = """
            CALL apoc.algo.pageRank([$node_id]) YIELD node, score
            WHERE id(node) = $node_id
            RETURN score as pagerank
            """
            pr_rows = neo4j_client.execute_cypher(pr_query, {"node_id": int(node_id)})
            if pr_rows and pr_rows[0].get("pagerank") is not None:
                metrics.pagerank = float(pr_rows[0]["pagerank"])
        except Exception:
            pass

        # Closeness centrality (simplified - distance to all reachable nodes)
        try:
            close_query = """
            MATCH (start) WHERE id(start) = $node_id
            MATCH path = shortestPath((start)-[*]-(target))
            WHERE target <> start
            WITH start, collect(DISTINCT length(path)) as distances
            WITH start, 
                 CASE WHEN size(distances) > 0 
                 THEN 1.0 / (sum(distances) / size(distances))
                 ELSE 0.0 END as closeness
            RETURN closeness
            """
            close_rows = neo4j_client.execute_cypher(close_query, {"node_id": int(node_id)})
            if close_rows and close_rows[0].get("closeness") is not None:
                metrics.closeness_centrality = float(close_rows[0]["closeness"])
        except Exception:
            pass

    return metrics


def compute_pagerank_for_subgraph(node_ids: List[str], iterations: int = 20) -> dict:
    """
    Compute PageRank for a subgraph of nodes.

    Returns dict mapping node_id to pagerank score.
    """
    if not node_ids:
        return {}

    try:
        query = """
        UNWIND $node_ids as node_id
        MATCH (n) WHERE id(n) = node_id
        WITH collect(n) as nodes
        CALL apoc.algo.pageRankWithConfig(nodes, {iterations: $iterations}) 
        YIELD node, score
        RETURN id(node) as node_id, score as pagerank
        """
        rows = neo4j_client.execute_cypher(
            query, {"node_ids": [int(nid) for nid in node_ids], "iterations": iterations}
        )
        return {str(row["node_id"]): float(row["pagerank"]) for row in rows}
    except Exception:
        # Fallback: simple degree-based ranking
        query = """
        UNWIND $node_ids as node_id
        MATCH (n) WHERE id(n) = node_id
        OPTIONAL MATCH (n)-[r]->()
        WITH n, count(r) as degree
        RETURN id(n) as node_id, degree as pagerank
        """
        rows = neo4j_client.execute_cypher(query, {"node_ids": [int(nid) for nid in node_ids]})
        return {str(row["node_id"]): float(row["pagerank"]) for row in rows}

"""Graph export for visualization."""
from typing import Dict, List, Optional

from .models import GraphNode, GraphRelationship, Subgraph


def export_subgraph_for_visualization(subgraph: Subgraph) -> Dict:
    """
    Export subgraph in format suitable for visualization libraries.

    Returns format compatible with D3.js, vis.js, cytoscape, etc.
    """
    nodes = [
        {
            "id": n.id,
            "label": n.properties.get("name") or n.id,
            "labels": n.labels,
            "properties": n.properties,
            # Include risk_score if available for frontend filtering
            "riskScore": n.properties.get("risk_score") or n.properties.get("riskScore"),
        }
        for n in subgraph.nodes
    ]

    edges = [
        {
            "id": f"{r.from_id}-{r.to_id}-{r.type}",
            "source": r.from_id,
            "target": r.to_id,
            "type": r.type,
            "properties": r.properties,
        }
        for r in subgraph.relationships
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "center_node_id": subgraph.center_node_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def export_path_for_visualization(path) -> Dict:
    """Export path in visualization format."""
    nodes = [
        {
            "id": n.id,
            "label": n.properties.get("name") or n.id,
            "labels": n.labels,
            "properties": n.properties,
            # Include risk_score if available for frontend filtering
            "riskScore": n.properties.get("risk_score") or n.properties.get("riskScore"),
        }
        for n in path.nodes
    ]

    edges = [
        {
            "id": f"{r.from_id}-{r.to_id}-{r.type}",
            "source": r.from_id,
            "target": r.to_id,
            "type": r.type,
            "properties": r.properties,
        }
        for r in path.relationships
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "length": path.length,
        "cost": path.cost,
    }


def export_cypher(subgraph: Subgraph) -> str:
    """Export subgraph as Cypher CREATE statements."""
    lines = []
    # Create nodes
    for node in subgraph.nodes:
        labels_str = ":".join(node.labels) if node.labels else "Node"
        props_str = ", ".join(f"{k}: {repr(v)}" for k, v in node.properties.items())
        if props_str:
            lines.append(f"CREATE (n{node.id}:{labels_str} {{{props_str}}})")
        else:
            lines.append(f"CREATE (n{node.id}:{labels_str})")

    # Create relationships
    for rel in subgraph.relationships:
        props_str = ", ".join(f"{k}: {repr(v)}" for k, v in rel.properties.items())
        if props_str:
            lines.append(f"CREATE (n{rel.from_id})-[:{rel.type} {{{props_str}}}]->(n{rel.to_id})")
        else:
            lines.append(f"CREATE (n{rel.from_id})-[:{rel.type}]->(n{rel.to_id})")

    return "\n".join(lines)

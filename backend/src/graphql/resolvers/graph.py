"""Graph traversal query resolvers."""
from typing import List, Optional
import strawberry
from strawberry.types import Info

from src.graph.relationship_search import find_connections
from src.graph.traversal import extract_subgraph, find_shortest_path
from src.graphql.resolvers.context import GraphQLContext
from src.graphql.types.relationship import PathType, RelationshipType
from src.graphql.types.business import BusinessType
from src.infrastructure.database.neo4j_client import neo4j_client


@strawberry.type
class GraphQuery:
    """Graph traversal queries."""

    @strawberry.field
    def connections(
        self,
        entity_a_id: str,
        entity_b_id: str,
        max_depth: int = 5,
        info: Info = None,
    ) -> List[PathType]:
        """Find connections between two entities."""
        context: GraphQLContext = info.context if info else None
        if context and not context.check_permission("read", "Business", entity_a_id):
            raise PermissionError("Not authorized")
        
        connections = find_connections(entity_a_id, entity_b_id, max_depth, include_all_paths=False)
        
        paths = []
        for conn in connections:
            rels = [
                RelationshipType(
                    type=r.type,
                    from_id=r.from_id,
                    to_id=r.to_id,
                    properties=str(r.properties) if r.properties else None,
                )
                for r in conn.path.relationships
            ]
            paths.append(
                PathType(
                    nodes=[n.id for n in conn.path.nodes],
                    relationships=rels,
                    length=conn.path.length,
                    strength_score=conn.strength_score,
                )
            )
        return paths

    @strawberry.field
    def subgraph(
        self,
        business_id: str,
        max_hops: int = 2,
        info: Info = None,
    ) -> List[BusinessType]:
        """Get subgraph around a business."""
        context: GraphQLContext = info.context if info else None
        if context and not context.check_permission("read", "Business", business_id):
            raise PermissionError("Not authorized")
        
        # Get Neo4j internal ID
        rows = neo4j_client.execute_cypher(
            "MATCH (b:Business {id: $business_id}) RETURN id(b) as node_id",
            {"business_id": business_id}
        )
        if not rows:
            return []
        
        node_id = str(rows[0]["node_id"])
        subgraph = extract_subgraph(node_id, max_hops=max_hops)
        
        # Convert to BusinessType (simplified - would handle all node types)
        businesses = []
        for node in subgraph.nodes:
            if "Business" in node.labels:
                business = Business.from_node_properties(node.properties)
                businesses.append(BusinessType.from_domain(business))
        return businesses

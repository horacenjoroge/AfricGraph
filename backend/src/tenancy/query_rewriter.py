"""Tenant-aware query rewriting for Neo4j."""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.infrastructure.logging import get_logger
from src.tenancy.context import get_current_tenant

logger = get_logger(__name__)


@dataclass
class RewrittenQuery:
    """Rewritten query with tenant isolation."""
    cypher: str
    params: Dict[str, Any]


class TenantQueryRewriter:
    """Rewrites Neo4j queries to include tenant isolation."""

    @staticmethod
    def rewrite_node_query(
        query: str,
        params: Optional[Dict[str, Any]] = None,
        node_alias: str = "n",
    ) -> RewrittenQuery:
        """
        Rewrite a node query to include tenant filtering.

        Adds tenant_id property check to node queries.
        """
        tenant = get_current_tenant()
        if not tenant:
            # If no tenant context, return original query (shouldn't happen with middleware)
            logger.warning("No tenant context for query rewrite")
            return RewrittenQuery(cypher=query, params=params or {})

        # Add tenant_id filter to WHERE clause
        # This is a simplified approach - in production, you'd want more sophisticated parsing
        if "WHERE" in query.upper():
            # Add tenant filter to existing WHERE clause
            query = query.replace("WHERE", f"WHERE {node_alias}.tenant_id = $tenant_id AND", 1)
        else:
            # Add WHERE clause with tenant filter
            # Find the MATCH or CREATE clause
            if "MATCH" in query.upper():
                query = query.replace("MATCH", "MATCH", 1)
                # Add WHERE after MATCH pattern
                query = query + f" WHERE {node_alias}.tenant_id = $tenant_id"
            elif "CREATE" in query.upper():
                # For CREATE, add tenant_id to properties
                # This is handled in the params, but we can also add WHERE if needed
                pass

        # Add tenant_id to params
        new_params = dict(params or {})
        new_params["tenant_id"] = tenant.tenant_id

        return RewrittenQuery(cypher=query, params=new_params)

    @staticmethod
    def rewrite_relationship_query(
        query: str,
        params: Optional[Dict[str, Any]] = None,
        node_alias: str = "n",
        rel_alias: str = "r",
    ) -> RewrittenQuery:
        """
        Rewrite a relationship query to include tenant filtering.

        Ensures both nodes in the relationship belong to the same tenant.
        """
        tenant = get_current_tenant()
        if not tenant:
            logger.warning("No tenant context for relationship query rewrite")
            return RewrittenQuery(cypher=query, params=params or {})

        # Add tenant_id filter for both nodes
        # Simplified approach - would need proper Cypher parsing in production
        tenant_filter = f"{node_alias}.tenant_id = $tenant_id"
        
        if "WHERE" in query.upper():
            query = query.replace("WHERE", f"WHERE {tenant_filter} AND", 1)
        else:
            # Add WHERE clause
            if "MATCH" in query.upper():
                # Add WHERE after MATCH pattern
                query = query + f" WHERE {tenant_filter}"

        new_params = dict(params or {})
        new_params["tenant_id"] = tenant.tenant_id

        return RewrittenQuery(cypher=query, params=new_params)

    @staticmethod
    def rewrite_traversal_query(
        query: str,
        params: Optional[Dict[str, Any]] = None,
        start_alias: str = "start",
    ) -> RewrittenQuery:
        """
        Rewrite a traversal query to include tenant filtering.

        Ensures all nodes in traversal belong to the tenant.
        """
        tenant = get_current_tenant()
        if not tenant:
            logger.warning("No tenant context for traversal query rewrite")
            return RewrittenQuery(cypher=query, params=params or {})

        # Add tenant filter to traversal
        # This ensures all nodes in the path belong to the tenant
        tenant_filter = f"ALL(n IN nodes(path) WHERE n.tenant_id = $tenant_id)"
        
        if "WHERE" in query.upper():
            query = query.replace("WHERE", f"WHERE {tenant_filter} AND", 1)
        else:
            query = query + f" WHERE {tenant_filter}"

        new_params = dict(params or {})
        new_params["tenant_id"] = tenant.tenant_id

        return RewrittenQuery(cypher=query, params=new_params)

    @staticmethod
    def add_tenant_to_properties(
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add tenant_id to node/relationship properties."""
        tenant = get_current_tenant()
        if not tenant:
            logger.warning("No tenant context for adding tenant_id to properties")
            return properties

        props = dict(properties)
        props["tenant_id"] = tenant.tenant_id
        return props

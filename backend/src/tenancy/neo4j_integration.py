"""Integration with Neo4j client for automatic tenant isolation."""
from typing import Dict, Any, Optional, List

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.tenancy.context import get_current_tenant
from src.tenancy.query_rewriter import TenantQueryRewriter

logger = get_logger(__name__)


def ensure_tenant_in_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure tenant_id is in properties for node/relationship creation."""
    tenant = get_current_tenant()
    if tenant:
        props = dict(properties)
        props["tenant_id"] = tenant.tenant_id
        return props
    return properties


def wrap_neo4j_operation(func):
    """Decorator to automatically add tenant isolation to Neo4j operations."""
    def wrapper(*args, **kwargs):
        # Add tenant_id to properties if creating/updating
        if "properties" in kwargs:
            kwargs["properties"] = ensure_tenant_in_properties(kwargs["properties"])
        elif "props" in kwargs:
            kwargs["props"] = ensure_tenant_in_properties(kwargs["props"])
        
        # Rewrite queries to include tenant filtering
        if "query" in kwargs:
            rewriter = TenantQueryRewriter()
            rewritten = rewriter.rewrite_node_query(kwargs["query"], kwargs.get("parameters"))
            kwargs["query"] = rewritten.cypher
            if "parameters" in kwargs:
                kwargs["parameters"].update(rewritten.params)
        
        return func(*args, **kwargs)
    return wrapper

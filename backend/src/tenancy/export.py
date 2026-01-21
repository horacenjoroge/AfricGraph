"""Data export functionality per tenant."""
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO
import json

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.logging import get_logger
from src.tenancy.context import get_current_tenant
from src.tenancy.manager import TenantManager

logger = get_logger(__name__)


class TenantDataExporter:
    """Exports tenant data for backup or migration."""

    def __init__(self):
        """Initialize exporter."""
        self.tenant_manager = TenantManager()

    def export_tenant_data(
        self,
        tenant_id: str,
        include_nodes: bool = True,
        include_relationships: bool = True,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Export all data for a tenant.

        Args:
            tenant_id: Tenant ID to export
            include_nodes: Include node data
            include_relationships: Include relationship data
            include_metadata: Include tenant metadata

        Returns:
            Dictionary with exported data
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")

        export_data = {
            "tenant_id": tenant_id,
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0",
        }

        if include_metadata:
            export_data["metadata"] = {
                "name": tenant.name,
                "domain": tenant.domain,
                "status": tenant.status,
                "config": tenant.config,
                "created_at": tenant.created_at.isoformat(),
            }

        if include_nodes:
            export_data["nodes"] = self._export_nodes(tenant_id)

        if include_relationships:
            export_data["relationships"] = self._export_relationships(tenant_id)

        return export_data

    def _export_nodes(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Export all nodes for a tenant."""
        query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN n
        """
        result = neo4j_client.execute_cypher(query, {"tenant_id": tenant_id})
        
        nodes = []
        for record in result:
            node_data = record.get("n", {})
            nodes.append({
                "id": node_data.get("id"),
                "labels": list(node_data.get("labels", [])),
                "properties": dict(node_data.get("properties", {})),
            })
        
        return nodes

    def _export_relationships(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Export all relationships for a tenant."""
        query = """
        MATCH (a)-[r]->(b)
        WHERE a.tenant_id = $tenant_id AND b.tenant_id = $tenant_id
        RETURN a.id as from_id, b.id as to_id, type(r) as rel_type, properties(r) as properties
        """
        result = neo4j_client.execute_cypher(query, {"tenant_id": tenant_id})
        
        relationships = []
        for record in result:
            relationships.append({
                "from_id": record.get("from_id"),
                "to_id": record.get("to_id"),
                "type": record.get("rel_type"),
                "properties": record.get("properties", {}),
            })
        
        return relationships

    def export_to_json(
        self,
        tenant_id: str,
        **kwargs,
    ) -> str:
        """Export tenant data as JSON string."""
        data = self.export_tenant_data(tenant_id, **kwargs)
        return json.dumps(data, indent=2, default=str)

    def export_to_file(
        self,
        tenant_id: str,
        file_path: str,
        **kwargs,
    ) -> str:
        """Export tenant data to JSON file."""
        json_data = self.export_to_json(tenant_id, **kwargs)
        with open(file_path, "w") as f:
            f.write(json_data)
        return file_path

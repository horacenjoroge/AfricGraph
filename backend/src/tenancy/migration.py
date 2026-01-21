"""Tenant migration tools."""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.tenancy.manager import TenantManager
from src.tenancy.export import TenantDataExporter

logger = get_logger(__name__)


class TenantMigrationManager:
    """Manages tenant data migration."""

    def __init__(self):
        """Initialize migration manager."""
        self.tenant_manager = TenantManager()
        self.exporter = TenantDataExporter()

    def migrate_tenant(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Migrate tenant data from source to target tenant.

        Args:
            source_tenant_id: Source tenant ID
            target_tenant_id: Target tenant ID (can be new)
            dry_run: If True, only simulate migration

        Returns:
            Migration statistics
        """
        source_tenant = self.tenant_manager.get_tenant(source_tenant_id)
        if not source_tenant:
            raise ValueError(f"Source tenant not found: {source_tenant_id}")

        # Ensure target tenant exists
        target_tenant = self.tenant_manager.get_tenant(target_tenant_id)
        if not target_tenant:
            # Create target tenant with same config
            target_tenant = self.tenant_manager.create_tenant(
                tenant_id=target_tenant_id,
                name=f"{source_tenant.name} (Migrated)",
                domain=None,
                config=source_tenant.config,
            )

        if dry_run:
            # Count nodes and relationships
            stats = self._count_tenant_data(source_tenant_id)
            return {
                "source_tenant_id": source_tenant_id,
                "target_tenant_id": target_tenant_id,
                "dry_run": True,
                "nodes_to_migrate": stats["nodes"],
                "relationships_to_migrate": stats["relationships"],
            }

        # Perform migration
        nodes_migrated = self._migrate_nodes(source_tenant_id, target_tenant_id)
        relationships_migrated = self._migrate_relationships(source_tenant_id, target_tenant_id)

        logger.info("Tenant migration completed", source=source_tenant_id, target=target_tenant_id)

        return {
            "source_tenant_id": source_tenant_id,
            "target_tenant_id": target_tenant_id,
            "nodes_migrated": nodes_migrated,
            "relationships_migrated": relationships_migrated,
            "status": "completed",
        }

    def _count_tenant_data(self, tenant_id: str) -> Dict[str, int]:
        """Count nodes and relationships for a tenant."""
        node_query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as count
        """
        node_result = neo4j_client.execute_cypher(node_query, {"tenant_id": tenant_id})
        node_count = node_result[0]["count"] if node_result else 0

        rel_query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        rel_result = neo4j_client.execute_cypher(rel_query, {"tenant_id": tenant_id})
        rel_count = rel_result[0]["count"] if rel_result else 0

        return {"nodes": node_count, "relationships": rel_count}

    def _migrate_nodes(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
    ) -> int:
        """Migrate nodes from source to target tenant."""
        # Get all nodes for source tenant
        query = """
        MATCH (n)
        WHERE n.tenant_id = $source_tenant_id
        RETURN n
        """
        nodes = neo4j_client.execute_cypher(query, {"source_tenant_id": source_tenant_id})

        migrated = 0
        for record in nodes:
            node_data = record.get("n", {})
            node_id = node_data.get("id")
            labels = node_data.get("labels", [])
            properties = dict(node_data.get("properties", {}))

            # Update tenant_id
            properties["tenant_id"] = target_tenant_id

            # Update node in Neo4j
            if labels and node_id:
                try:
                    neo4j_client.merge_node(
                        label=labels[0],
                        id_val=node_id,
                        props=properties,
                    )
                    migrated += 1
                except Exception as e:
                    logger.exception("Failed to migrate node", node_id=node_id, error=str(e))

        return migrated

    def _migrate_relationships(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
    ) -> int:
        """Migrate relationships from source to target tenant."""
        # Relationships are migrated automatically when nodes are migrated
        # But we need to update relationship tenant_id if it's stored
        query = """
        MATCH (a)-[r]->(b)
        WHERE a.tenant_id = $target_tenant_id AND b.tenant_id = $target_tenant_id
        AND r.tenant_id = $source_tenant_id
        SET r.tenant_id = $target_tenant_id
        RETURN count(r) as count
        """
        result = neo4j_client.execute_cypher(query, {
            "source_tenant_id": source_tenant_id,
            "target_tenant_id": target_tenant_id,
        })

        return result[0]["count"] if result else 0

    def clone_tenant(
        self,
        source_tenant_id: str,
        new_tenant_id: str,
        new_name: str,
    ) -> Dict[str, Any]:
        """
        Clone a tenant (create copy with new ID).

        Args:
            source_tenant_id: Source tenant to clone
            new_tenant_id: New tenant ID
            new_name: Name for new tenant

        Returns:
            Clone statistics
        """
        return self.migrate_tenant(
            source_tenant_id=source_tenant_id,
            target_tenant_id=new_tenant_id,
            dry_run=False,
        )

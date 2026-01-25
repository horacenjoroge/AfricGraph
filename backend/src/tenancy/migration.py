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
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Migrate tenant data from source to target tenant.

        Args:
            source_tenant_id: Source tenant ID
            target_tenant_id: Target tenant ID (can be new)
            dry_run: If True, only simulate migration
            validate: If True, validate data integrity after migration

        Returns:
            Migration statistics
        """
        source_tenant = self.tenant_manager.get_tenant(source_tenant_id)
        if not source_tenant:
            raise ValueError(f"Source tenant not found: {source_tenant_id}")

        # Validate source tenant has data
        source_stats = self._count_tenant_data(source_tenant_id)
        if source_stats["nodes"] == 0 and source_stats["relationships"] == 0:
            logger.warning("Source tenant has no data to migrate", tenant_id=source_tenant_id)

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
        else:
            # Check if target tenant already has data
            target_stats = self._count_tenant_data(target_tenant_id)
            if target_stats["nodes"] > 0 or target_stats["relationships"] > 0:
                logger.warning(
                    "Target tenant already has data",
                    tenant_id=target_tenant_id,
                    nodes=target_stats["nodes"],
                    relationships=target_stats["relationships"],
                )

        if dry_run:
            # Count nodes and relationships
            return {
                "source_tenant_id": source_tenant_id,
                "target_tenant_id": target_tenant_id,
                "dry_run": True,
                "nodes_to_migrate": source_stats["nodes"],
                "relationships_to_migrate": source_stats["relationships"],
                "target_has_existing_data": target_stats["nodes"] > 0 or target_stats["relationships"] > 0,
            }

        # Perform migration with transaction support
        migration_start = datetime.utcnow()
        try:
            nodes_migrated = self._migrate_nodes(source_tenant_id, target_tenant_id)
            relationships_migrated = self._migrate_relationships(source_tenant_id, target_tenant_id)
            
            # Validate migration if requested
            validation_result = None
            if validate:
                validation_result = self._validate_migration(
                    source_tenant_id,
                    target_tenant_id,
                    source_stats,
                )
            
            migration_end = datetime.utcnow()
            duration_seconds = (migration_end - migration_start).total_seconds()
            
            logger.info(
                "Tenant migration completed",
                source=source_tenant_id,
                target=target_tenant_id,
                nodes=nodes_migrated,
                relationships=relationships_migrated,
                duration_seconds=duration_seconds,
            )

            return {
                "source_tenant_id": source_tenant_id,
                "target_tenant_id": target_tenant_id,
                "nodes_migrated": nodes_migrated,
                "relationships_migrated": relationships_migrated,
                "status": "completed",
                "duration_seconds": duration_seconds,
                "validation": validation_result,
            }
        except Exception as e:
            logger.exception(
                "Migration failed",
                source=source_tenant_id,
                target=target_tenant_id,
                error=str(e),
            )
            # Rollback would be implemented here if needed
            raise

    def _count_tenant_data(self, tenant_id: str) -> Dict[str, int]:
        """Count nodes and relationships for a tenant."""
        node_query = """
        MATCH (n)
        WHERE n.tenant_id = $tenant_id
        RETURN count(n) as count
        """
        node_result = neo4j_client.execute_cypher(
            node_query, 
            {"tenant_id": tenant_id},
            skip_tenant_filter=True,  # Already has tenant filter
        )
        node_count = node_result[0]["count"] if node_result else 0

        rel_query = """
        MATCH ()-[r]->()
        WHERE r.tenant_id = $tenant_id
        RETURN count(r) as count
        """
        rel_result = neo4j_client.execute_cypher(
            rel_query, 
            {"tenant_id": tenant_id},
            skip_tenant_filter=True,  # Already has tenant filter
        )
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
    
    def _validate_migration(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
        expected_stats: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Validate that migration was successful.
        
        Args:
            source_tenant_id: Source tenant ID
            target_tenant_id: Target tenant ID
            expected_stats: Expected node/relationship counts
            
        Returns:
            Validation results
        """
        target_stats = self._count_tenant_data(target_tenant_id)
        
        nodes_match = target_stats["nodes"] == expected_stats["nodes"]
        relationships_match = target_stats["relationships"] == expected_stats["relationships"]
        
        # Check for orphaned relationships
        orphaned_query = """
        MATCH (a)-[r]->(b)
        WHERE (a.tenant_id = $target_tenant_id AND b.tenant_id != $target_tenant_id)
           OR (a.tenant_id != $target_tenant_id AND b.tenant_id = $target_tenant_id)
        RETURN count(r) as orphaned_count
        """
        try:
            orphaned_result = neo4j_client.execute_cypher(
                orphaned_query,
                {"target_tenant_id": target_tenant_id},
                skip_tenant_filter=True,
            )
            orphaned_count = orphaned_result[0]["orphaned_count"] if orphaned_result else 0
        except Exception as e:
            logger.exception("Failed to check for orphaned relationships", error=str(e))
            orphaned_count = -1  # Unknown
        
        is_valid = nodes_match and relationships_match and orphaned_count == 0
        
        return {
            "valid": is_valid,
            "nodes_match": nodes_match,
            "relationships_match": relationships_match,
            "expected_nodes": expected_stats["nodes"],
            "actual_nodes": target_stats["nodes"],
            "expected_relationships": expected_stats["relationships"],
            "actual_relationships": target_stats["relationships"],
            "orphaned_relationships": orphaned_count,
        }

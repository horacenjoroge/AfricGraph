"""Tenant management and isolation."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger
from src.tenancy.models import Tenant, TenantConfig, TenantStats

logger = get_logger(__name__)


class TenantManager:
    """Manages tenants and tenant isolation."""

    def __init__(self):
        """Initialize tenant manager."""
        self._tables_ensured = False

    def _ensure_tenant_tables(self):
        """Ensure tenant tables exist in PostgreSQL."""
        query = """
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255),
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            config JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS tenant_configs (
            tenant_id VARCHAR(255) NOT NULL,
            key VARCHAR(255) NOT NULL,
            value JSONB NOT NULL,
            description TEXT,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            PRIMARY KEY (tenant_id, key),
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
        CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain);
        """
        with postgres_client.get_session() as session:
            session.execute(text(query))
            session.commit()

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier
            name: Tenant name
            domain: Optional domain
            config: Optional initial configuration

        Returns:
            Tenant instance
        """
        if not self._tables_ensured:
            self._ensure_tenant_tables()
            self._tables_ensured = True
        now = datetime.now(timezone.utc)
        query = """
        INSERT INTO tenants (tenant_id, name, domain, status, config, created_at, updated_at)
        VALUES (%(tenant_id)s, %(name)s, %(domain)s, 'active', %(config)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (tenant_id) DO UPDATE
        SET name = EXCLUDED.name,
            domain = EXCLUDED.domain,
            updated_at = EXCLUDED.updated_at
        """
        params = {
            "tenant_id": tenant_id,
            "name": name,
            "domain": domain,
            "config": config or {},
            "created_at": now,
            "updated_at": now,
        }
        with postgres_client.get_session() as session:
            session.execute(text(query), params)
            session.commit()

        logger.info("Tenant created", tenant_id=tenant_id, name=name)
        return self.get_tenant(tenant_id)

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        if not self._tables_ensured:
            self._ensure_tenant_tables()
            self._tables_ensured = True
        query = "SELECT tenant_id, name, domain, status, config, created_at, updated_at FROM tenants WHERE tenant_id = %(tenant_id)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"tenant_id": tenant_id})
            row = result.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            return Tenant(
                tenant_id=row_dict["tenant_id"],
                name=row_dict["name"],
                domain=row_dict.get("domain"),
                status=row_dict["status"],
                config=row_dict.get("config") or {},
                created_at=row_dict["created_at"],
                updated_at=row_dict["updated_at"],
            )

    def list_tenants(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Tenant]:
        """List tenants with optional status filter."""
        conditions = ["1=1"]
        params = {"limit": limit}

        if status:
            conditions.append("status = %(status)s")
            params["status"] = status

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT tenant_id, name, domain, status, config, created_at, updated_at
        FROM tenants
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %(limit)s
        """
        
        with postgres_client.get_session() as session:
            result = session.execute(text(query), params)
            rows = [dict(row) for row in result]
        
        return [
            Tenant(
                tenant_id=row["tenant_id"],
                name=row["name"],
                domain=row.get("domain"),
                status=row["status"],
                config=row.get("config") or {},
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tenant]:
        """Update tenant."""
        updates = []
        params = {"tenant_id": tenant_id, "updated_at": datetime.now(timezone.utc)}

        if name is not None:
            updates.append("name = %(name)s")
            params["name"] = name

        if domain is not None:
            updates.append("domain = %(domain)s")
            params["domain"] = domain

        if status is not None:
            updates.append("status = %(status)s")
            params["status"] = status

        if config is not None:
            updates.append("config = %(config)s")
            params["config"] = config

        if not updates:
            return self.get_tenant(tenant_id)

        updates.append("updated_at = %(updated_at)s")
        set_clause = ", ".join(updates)

        query = f"""
        UPDATE tenants
        SET {set_clause}
        WHERE tenant_id = %(tenant_id)s
        """
        
        with postgres_client.get_session() as session:
            session.execute(text(query), params)
            session.commit()

        logger.info("Tenant updated", tenant_id=tenant_id)
        return self.get_tenant(tenant_id)

    def set_tenant_config(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        description: Optional[str] = None,
    ) -> TenantConfig:
        """Set tenant-specific configuration."""
        query = """
        INSERT INTO tenant_configs (tenant_id, key, value, description, updated_at)
        VALUES (%(tenant_id)s, %(key)s, %(value)s, %(description)s, NOW())
        ON CONFLICT (tenant_id, key) DO UPDATE
        SET value = EXCLUDED.value,
            description = EXCLUDED.description,
            updated_at = NOW()
        """
        params = {
            "tenant_id": tenant_id,
            "key": key,
            "value": value,
            "description": description,
        }
        with postgres_client.get_session() as session:
            session.execute(text(query), params)
            session.commit()

        return TenantConfig(
            tenant_id=tenant_id,
            key=key,
            value=value,
            description=description,
            updated_at=datetime.now(timezone.utc),
        )

    def get_tenant_config(self, tenant_id: str, key: str) -> Optional[Any]:
        """Get tenant-specific configuration value."""
        query = "SELECT value FROM tenant_configs WHERE tenant_id = %(tenant_id)s AND key = %(key)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"tenant_id": tenant_id, "key": key})
            row = result.fetchone()
            return row["value"] if row else None

    def get_all_tenant_configs(self, tenant_id: str) -> Dict[str, Any]:
        """Get all tenant configurations."""
        query = "SELECT key, value FROM tenant_configs WHERE tenant_id = %(tenant_id)s"
        with postgres_client.get_session() as session:
            result = session.execute(text(query), {"tenant_id": tenant_id})
            return {row["key"]: row["value"] for row in result}

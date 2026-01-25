# Multi-Tenancy Support

This module provides multi-tenancy support, allowing multiple organizations to use the same AfricGraph instance with complete data isolation.

## Features

- **Tenant Isolation**: Complete data isolation between tenants
- **Tenant-Aware Queries**: All queries automatically filtered by tenant
- **Tenant-Specific Configs**: Per-tenant configuration
- **Cross-Tenant Analytics**: Aggregated analytics (no individual tenant data)
- **Data Export**: Export all data for a tenant
- **Tenant Migration**: Migrate tenant data between instances with validation
- **Performance Optimization**: Indexes for tenant_id on all node labels
- **Data Leak Prevention**: Query validation and security checks
- **Monitoring & Health**: Tenant health monitoring and resource usage tracking

## Architecture

### Tenant Identification

Tenants are identified via:
1. **X-Tenant-ID Header**: Explicit tenant ID in request header
2. **Subdomain**: Tenant subdomain (e.g., `tenant1.africgraph.com`)
3. **JWT Token**: Tenant ID in JWT token (if implemented)

### Data Isolation

- **Neo4j**: All nodes and relationships have `tenant_id` property
- **PostgreSQL**: All tables include `tenant_id` column
- **Query Rewriting**: All queries automatically filtered by tenant

### Security

- **Middleware**: Tenant context set before request processing
- **Query Filtering**: All database queries include tenant filter
- **Data Leak Prevention**: Multiple layers of tenant isolation

## Usage

### Creating a Tenant

```python
from src.tenancy.manager import TenantManager

manager = TenantManager()
tenant = manager.create_tenant(
    tenant_id="acme-corp",
    name="Acme Corporation",
    domain="acme.africgraph.com",
)
```

### Setting Tenant Context

Tenant context is automatically set by middleware from:
- Request headers (`X-Tenant-ID`)
- Subdomain
- JWT token

### Querying with Tenant Isolation

All Neo4j queries are automatically filtered:

```python
# This query automatically includes tenant_id filter
nodes = neo4j_client.find_nodes(label="Business")
# Only returns nodes for current tenant
```

### Tenant-Specific Configuration

```python
manager.set_tenant_config(
    tenant_id="acme-corp",
    key="max_nodes",
    value=10000,
    description="Maximum nodes allowed",
)
```

### Exporting Tenant Data

```python
from src.tenancy.export import TenantDataExporter

exporter = TenantDataExporter()
data = exporter.export_tenant_data(tenant_id="acme-corp")
```

### Migrating Tenant

```python
from src.tenancy.migration import TenantMigrationManager

migration = TenantMigrationManager()
result = migration.migrate_tenant(
    source_tenant_id="acme-corp",
    target_tenant_id="acme-corp-new",
    dry_run=True,  # Test first
)
```

## API Endpoints

### Tenant Management

- `POST /tenants` - Create tenant
- `GET /tenants/{id}` - Get tenant
- `GET /tenants` - List tenants
- `PUT /tenants/{id}` - Update tenant

### Tenant Configuration

- `POST /tenants/{id}/config` - Set config
- `GET /tenants/{id}/config` - Get configs

### Data Operations

- `GET /tenants/{id}/export` - Export tenant data
- `POST /tenants/migrate` - Migrate tenant

### Analytics

- `GET /tenants/analytics/aggregated` - Cross-tenant aggregated statistics
- `GET /tenants/analytics/distribution?metric=nodes` - Tenant distribution by metric
- `GET /tenants/analytics/activity?days=30` - Aggregated activity summary

### Monitoring

- `GET /tenants/{id}/health` - Get tenant health metrics
- `GET /tenants/{id}/usage?days=30` - Get tenant resource usage
- `GET /tenants/health/all` - Get health status for all tenants

### Index Management

- `POST /tenants/indexes/ensure` - Ensure all tenant indexes exist
- `GET /tenants/indexes/status` - Get status of tenant-related indexes

## Performance Considerations

### With Many Tenants

1. **Indexes**: Ensure `tenant_id` is indexed on all node labels
   - Run: `python scripts/ensure_tenant_indexes.py`
   - Or use API: `POST /tenants/indexes/ensure`
2. **Query Optimization**: Tenant filters added early in query execution
3. **Caching**: Cache tenant configs and stats (implemented in manager)
4. **Composite Indexes**: Created for common query patterns (tenant_id + other filters)
5. **Monitoring**: Track query performance per tenant

### Index Creation

```bash
# Create all tenant isolation indexes
python scripts/ensure_tenant_indexes.py

# Or via API (requires admin)
curl -X POST http://localhost:8000/tenants/indexes/ensure \
  -H "Authorization: Bearer <admin_token>"
```

### Storage

- Each tenant's data is stored in the same database
- `tenant_id` property/column used for isolation
- Consider archiving inactive tenants

## Security Best Practices

1. **Always Validate Tenant**: Middleware ensures tenant context
2. **Query Rewriting**: All queries include tenant filter
3. **Query Validation**: TenantSecurityValidator checks for unsafe patterns
4. **Audit Logging**: Log all tenant operations
5. **Access Control**: Combine with ABAC for fine-grained control
6. **Data Leak Prevention**: Multiple layers of validation

### Security Features

- **Query Validation**: Detects patterns that could bypass tenant filtering
- **Context Verification**: Ensures tenant context is set before data access
- **Access Control**: Validates user permissions for tenant operations
- **Audit Trail**: All queries are logged for security monitoring

## Migration

### Tenant Migration Process

1. Export source tenant data
2. Create target tenant
3. Import data to target tenant
4. Verify data integrity
5. Update application references
6. Deactivate source tenant

### Data Export Format

```json
{
  "tenant_id": "acme-corp",
  "exported_at": "2024-01-15T10:00:00Z",
  "version": "1.0",
  "metadata": {
    "name": "Acme Corporation",
    "status": "active"
  },
  "nodes": [...],
  "relationships": [...]
}
```

## Limitations

- **Storage Growth**: All tenants share same database
- **Performance**: Many tenants can impact query performance
- **Backup**: Tenant-specific backups require filtering

## Future Enhancements

- [ ] Tenant-specific database schemas
- [ ] Tenant resource quotas
- [ ] Automatic tenant provisioning
- [ ] Tenant billing integration
- [ ] Cross-tenant collaboration (with permissions)

# Multi-Tenancy System Testing Guide

## Overview

The multi-tenancy system is now production-ready with comprehensive features for isolation, performance optimization, security, monitoring, quotas, and billing.

## Quick Start

### 1. Create Indexes

```bash
# Ensure all tenant isolation indexes are created
python3 backend/scripts/ensure_tenant_indexes.py
```

Or via API (requires admin):
```bash
curl -X POST http://localhost:8000/tenants/indexes/ensure \
  -H "Authorization: Bearer <admin_token>"
```

### 2. Run System Tests

```bash
# Run automated test script
python3 backend/scripts/test_tenancy_system.py

# Or run pytest tests
pytest backend/tests/integration/test_tenant_isolation.py -v
```

### 3. Manual Testing

#### Create Multiple Tenants

```bash
# Create tenant 1
curl -X POST http://localhost:8000/tenants \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme-corp",
    "name": "Acme Corporation",
    "domain": "acme.africgraph.com"
  }'

# Create tenant 2
curl -X POST http://localhost:8000/tenants \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tech-startup",
    "name": "Tech Startup Inc",
    "domain": "tech.africgraph.com"
  }'
```

#### Verify Data Isolation

1. Create data for tenant 1:
```bash
curl -X POST http://localhost:8000/api/v1/businesses \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BIZ001",
    "name": "Acme Business",
    "registration_number": "REG123"
  }'
```

2. Query as tenant 1 (should see the business):
```bash
curl http://localhost:8000/api/v1/businesses/BIZ001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp"
```

3. Query as tenant 2 (should NOT see the business):
```bash
curl http://localhost:8000/api/v1/businesses/BIZ001 \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tech-startup"
# Should return 404 or empty result
```

#### Check Analytics Endpoints

```bash
# Aggregated analytics (admin only)
curl http://localhost:8000/tenants/analytics/aggregated \
  -H "Authorization: Bearer <admin_token>"

# Tenant distribution
curl http://localhost:8000/tenants/analytics/distribution?metric=nodes \
  -H "Authorization: Bearer <admin_token>"

# Activity summary
curl http://localhost:8000/tenants/analytics/activity?days=30 \
  -H "Authorization: Bearer <admin_token>"
```

#### Monitor Tenant Health

```bash
# Get tenant health
curl http://localhost:8000/tenants/acme-corp/health \
  -H "Authorization: Bearer <admin_token>"

# Get tenant usage
curl http://localhost:8000/tenants/acme-corp/usage?days=30 \
  -H "Authorization: Bearer <admin_token>"

# Get all tenants health
curl http://localhost:8000/tenants/health/all \
  -H "Authorization: Bearer <admin_token>"
```

#### Check Quotas

```bash
# Get tenant quotas
curl http://localhost:8000/tenants/acme-corp/quotas \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp"

# Set quota limit (admin only)
curl -X PUT "http://localhost:8000/tenants/acme-corp/quotas/nodes?limit=50000" \
  -H "Authorization: Bearer <admin_token>"
```

#### Check Billing

```bash
# Get usage summary
curl http://localhost:8000/tenants/acme-corp/billing/usage \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: acme-corp"

# Calculate bill (admin only)
curl http://localhost:8000/tenants/acme-corp/billing/calculate \
  -H "Authorization: Bearer <admin_token>"

# Set billing plan (admin only)
curl -X PUT "http://localhost:8000/tenants/acme-corp/billing/plan?plan_id=pro" \
  -H "Authorization: Bearer <admin_token>"
```

## Automated Tests

### Run All Tenant Tests

```bash
pytest backend/tests/integration/test_tenant_isolation.py -v
```

### Test Coverage

The test suite covers:
- ✅ Tenant creation and management
- ✅ Data isolation (nodes and relationships)
- ✅ Query rewriter tenant filtering
- ✅ Cross-tenant data leak prevention
- ✅ Tenant config isolation
- ✅ Tenant migration isolation
- ✅ Analytics aggregation (no data leaks)
- ✅ Tenant export isolation

## Features Implemented

### ✅ Core Features
1. **Tenant Isolation** - Complete data isolation between tenants
2. **Index Management** - Performance indexes for tenant_id
3. **Monitoring** - Health and usage tracking
4. **Security** - Query validation and data leak prevention
5. **Analytics** - Cross-tenant aggregated analytics
6. **Migration** - Tenant data migration with validation

### ✅ Enhanced Features
1. **Resource Quotas** - Per-tenant quota limits and tracking
2. **Billing Integration** - Usage tracking and billing plans
3. **Performance Dashboard** - Frontend dashboard for tenant metrics
4. **Comprehensive Tests** - Automated test suite

## API Endpoints Summary

### Tenant Management
- `POST /tenants` - Create tenant
- `GET /tenants` - List tenants (admin)
- `GET /tenants/{id}` - Get tenant
- `PUT /tenants/{id}` - Update tenant
- `GET /tenants/available` - List available tenants

### Monitoring
- `GET /tenants/{id}/health` - Tenant health
- `GET /tenants/{id}/usage` - Resource usage
- `GET /tenants/health/all` - All tenants health

### Analytics
- `GET /tenants/analytics/aggregated` - Aggregated stats
- `GET /tenants/analytics/distribution` - Tenant distribution
- `GET /tenants/analytics/activity` - Activity summary

### Indexes
- `POST /tenants/indexes/ensure` - Create indexes
- `GET /tenants/indexes/status` - Index status

### Quotas
- `GET /tenants/{id}/quotas` - Get quotas
- `PUT /tenants/{id}/quotas/{type}` - Set quota limit

### Billing
- `GET /tenants/{id}/billing/usage` - Usage summary
- `GET /tenants/{id}/billing/calculate` - Calculate bill
- `PUT /tenants/{id}/billing/plan` - Set billing plan

## Next Steps

1. **Run Index Creation**: `python3 backend/scripts/ensure_tenant_indexes.py`
2. **Run Tests**: `pytest backend/tests/integration/test_tenant_isolation.py`
3. **Test System**: `python3 backend/scripts/test_tenancy_system.py`
4. **Monitor Health**: Use the API endpoints or frontend dashboard
5. **Set Quotas**: Configure per-tenant resource limits
6. **Configure Billing**: Set up billing plans for tenants

## Production Checklist

- [ ] Indexes created for all node labels
- [ ] Tenant isolation verified
- [ ] Security validation enabled
- [ ] Monitoring configured
- [ ] Quotas configured per tenant
- [ ] Billing plans assigned
- [ ] Automated tests passing
- [ ] Performance dashboard accessible
- [ ] Backup strategy in place
- [ ] Documentation updated

## Troubleshooting

### Indexes Not Created
```bash
# Check index status
curl http://localhost:8000/tenants/indexes/status \
  -H "Authorization: Bearer <admin_token>"

# Create indexes
python3 backend/scripts/ensure_tenant_indexes.py
```

### Data Isolation Issues
- Verify tenant context is set in requests (X-Tenant-ID header)
- Check query rewriter is adding tenant filters
- Review security validator logs
- Run isolation tests: `pytest backend/tests/integration/test_tenant_isolation.py`

### Performance Issues
- Ensure indexes are created
- Check query performance per tenant
- Review quota usage
- Monitor resource usage via API

## Support

For issues or questions:
1. Check logs: `backend/logs/`
2. Review test results
3. Check API documentation: `http://localhost:8000/docs`
4. Review tenant health endpoints

# AfricGraph Testing Guide

This guide provides comprehensive instructions for testing the AfricGraph system.

## Prerequisites

1. **Services Running:**
   - Neo4j (port 7687)
   - PostgreSQL (port 5433)
   - Redis (port 6379)
   - RabbitMQ (port 5672)
   - Elasticsearch (port 9200)
   - Backend API (port 8000)
   - Frontend (port 3000)

2. **Environment Setup:**
   ```bash
   cd backend
   source venv/bin/activate
   ```

## Quick Start

### 1. Seed Sample Data

Populate the database with test data:

```bash
cd backend
python scripts/seed_data.py
```

This creates:
- 20 sample businesses
- 15 sample people
- Ownership relationships
- Supplier relationships
- Director relationships
- 50 sample transactions

### 2. Run System Tests

```bash
cd backend
./scripts/test_system.sh
```

This tests:
- API health
- Business search
- Business creation/retrieval
- Audit logs
- Risk assessment
- Graph traversal

## Manual Testing Checklist

### Backend API Testing

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected: All services show as "healthy"

#### 2. Business Search
```bash
# Search all businesses
curl http://localhost:8000/api/v1/businesses/search

# Search with query
curl "http://localhost:8000/api/v1/businesses/search?query=Tech"

# Search with sector filter
curl "http://localhost:8000/api/v1/businesses/search?sector=Technology"
```

#### 3. Business CRUD
```bash
# Create business
curl -X POST http://localhost:8000/api/v1/businesses \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BIZ001",
    "name": "Test Company",
    "sector": "Technology",
    "registration_number": "REG123456"
  }'

# Get business
curl http://localhost:8000/api/v1/businesses/BIZ001

# Get business graph
curl "http://localhost:8000/api/v1/businesses/BIZ001/graph?max_hops=2"
```

#### 4. Risk Assessment
```bash
curl http://localhost:8000/api/v1/risk/BIZ001
```

#### 5. Fraud Alerts
```bash
curl http://localhost:8000/api/v1/fraud/alerts
```

#### 6. Workflows
```bash
curl http://localhost:8000/api/v1/workflows
```

#### 7. Audit Logs
```bash
curl "http://localhost:8000/api/v1/audit?limit=100"
```

#### 8. Graph Traversal
```bash
# Get subgraph
curl "http://localhost:8000/api/v1/graph/subgraph/BIZ001?max_hops=2&format=json"

# Find relationships
curl "http://localhost:8000/api/v1/relationships?entity_a=BIZ001&entity_b=BIZ002"
```

### Frontend Testing

1. **Open the application:**
   ```
   http://localhost:3000
   ```

2. **Test each page:**
   - ✅ Dashboard - Check KPIs and charts load
   - ✅ Business Search - Search for businesses, test filters
   - ✅ Business Detail - Click on a business, view details
   - ✅ Graph Explorer - Load graph, interact with nodes
   - ✅ Risk Analysis - Enter business ID, view risk scores
   - ✅ Fraud Alerts - View alerts, acknowledge them
   - ✅ Workflows - View and manage workflows
   - ✅ Audit Logs - Browse audit history
   - ✅ Settings - Check settings page

3. **Test Features:**
   - ✅ Theme toggle (light/dark mode)
   - ✅ Tenant selector (switch tenants)
   - ✅ Error notifications (try invalid searches)
   - ✅ Loading states
   - ✅ Responsive design

### Integration Testing

#### Test Business Flow
1. Create a business via API
2. Search for it in frontend
3. View its details
4. Check risk assessment
5. View in graph explorer
6. Check audit logs for actions

#### Test Relationship Flow
1. Create two businesses
2. Create a person
3. Create ownership relationship
4. Search for relationships in frontend
5. View in graph explorer

#### Test Error Handling
1. Search for non-existent business
2. Try invalid API calls
3. Check error notifications appear
4. Verify error messages are user-friendly

## Load Testing

Use Locust for load testing:

```bash
cd backend
locust -f tests/load/test_api_load.py --host=http://localhost:8000
```

Then open http://localhost:8089 to run load tests.

## Performance Testing

### Check API Response Times
```bash
# Time a search request
time curl -s "http://localhost:8000/api/v1/businesses/search?query=Tech" > /dev/null
```

### Check Database Performance
```bash
# In Neo4j browser (http://localhost:7474)
MATCH (n) RETURN count(n) as total_nodes
MATCH ()-[r]->() RETURN count(r) as total_relationships
```

## Security Testing

1. **Test Authentication:**
   ```bash
   # Try accessing protected endpoint without token
   curl http://localhost:8000/api/v1/businesses
   ```

2. **Test Tenant Isolation:**
   - Switch tenants in frontend
   - Verify data is isolated
   - Check tenant-specific queries

3. **Test ABAC Permissions:**
   - Test with different user roles
   - Verify permission checks work
   - Check audit logs record decisions

## Troubleshooting

### Common Issues

1. **404 Errors:**
   - Check route order in backend
   - Verify endpoint paths match
   - Check API versioning

2. **403 Errors:**
   - Check tenant middleware
   - Verify tenant context is set
   - Check ABAC permissions

3. **Empty Results:**
   - Run seed data script
   - Check database connections
   - Verify data exists in Neo4j

4. **Frontend Not Loading:**
   - Check API proxy settings
   - Verify CORS configuration
   - Check browser console for errors

## Test Data

After running `seed_data.py`, you'll have:

- **Businesses:** BIZ001-BIZ020
- **People:** PERSON001-PERSON015
- **Relationships:** Ownership, supplier, director
- **Transactions:** 50 sample transactions

Use these IDs for testing specific scenarios.

## Next Steps

1. Run automated tests: `pytest tests/`
2. Check test coverage: `pytest --cov=src tests/`
3. Review API documentation: http://localhost:8000/docs
4. Check system metrics: http://localhost:8000/metrics

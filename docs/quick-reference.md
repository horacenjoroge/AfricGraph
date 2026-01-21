# Quick Reference Guide

Quick reference for common commands and operations.

## Docker Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Execute command in container
docker exec -it africgraph-backend bash
```

## API Quick Reference

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
export TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/businesses/123
```

### Common Endpoints

```bash
# Get business
GET /api/v1/businesses/{id}

# Search businesses
GET /api/v1/businesses/search?query=acme

# Get risk assessment
GET /api/v1/risk/{business_id}

# Run fraud scan
POST /api/v1/fraud/business/{business_id}/scan

# Get graph
GET /api/v1/businesses/{id}/graph?max_hops=2

# Health check
GET /health
```

## GraphQL Quick Reference

### Common Queries

```graphql
# Get business
query {
  business(id: "business-123") {
    id
    name
    riskScore
  }
}

# Search businesses
query {
  businesses(query: "acme", limit: 20) {
    id
    name
  }
}

# Get risk assessment
query {
  business(id: "business-123") {
    riskAssessment {
      compositeScore
      factorScores {
        name
        score
      }
    }
  }
}
```

## Database Quick Reference

### Neo4j

```cypher
# Count nodes
MATCH (n) RETURN count(n)

# Find business
MATCH (b:Business {id: "business-123"}) RETURN b

# Find relationships
MATCH (a:Business)-[r:OWNS]->(b:Business) RETURN a, r, b

# Shortest path
MATCH path = shortestPath((a:Business {id: "1"})-[*]-(b:Business {id: "2"})) RETURN path
```

### PostgreSQL

```sql
-- List tables
\dt

-- Query audit logs
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;

-- Check user count
SELECT COUNT(*) FROM users;
```

## Scripts Quick Reference

```bash
# Deploy
./deployment/scripts/deploy.sh production

# Update
./deployment/scripts/update.sh production

# Backup
./deployment/scripts/backup-enhanced.sh full

# Restore
./deployment/scripts/restore-enhanced.sh /path/to/backup

# Health check
./deployment/scripts/health-check.sh

# View logs
./deployment/scripts/logs.sh backend

# List backups
./deployment/scripts/list-backups.sh

# Test backup
./deployment/scripts/test-backup.sh /path/to/backup
```

## Testing Quick Reference

```bash
# Run all tests
pytest

# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/unit/test_risk_scoring.py::TestFactorScore

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Monitoring Quick Reference

```bash
# View metrics
curl http://localhost:8000/metrics

# Check health
curl http://localhost:8000/health

# Docker stats
docker stats

# System resources
top
df -h
free -h
```

## Environment Variables

```bash
# Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=your_password
POSTGRES_HOST=postgres
POSTGRES_DB=africgraph
POSTGRES_PASSWORD=your_password

# API
JWT_SECRET_KEY=your_secret_key
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=INFO
```

## Ports Reference

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| Frontend | 3000 | React development server |
| Neo4j Browser | 7474 | Neo4j web interface |
| Neo4j Bolt | 7687 | Neo4j protocol |
| PostgreSQL | 5432 | PostgreSQL database |
| Redis | 6379 | Redis cache |
| RabbitMQ | 5672 | AMQP protocol |
| RabbitMQ Management | 15672 | Management UI |
| Elasticsearch | 9200 | Elasticsearch API |

## File Locations

| Item | Location |
|------|----------|
| Application Code | `/opt/africgraph` |
| Backups | `/var/backups/africgraph` |
| Logs | `/opt/africgraph/logs` |
| Nginx Config | `/etc/nginx/sites-available/africgraph.conf` |
| SSL Certificates | `/etc/letsencrypt/live/yourdomain.com/` |
| Environment | `/opt/africgraph/.env` |

## Common Issues Quick Fix

| Issue | Quick Fix |
|-------|-----------|
| Service won't start | `docker-compose restart service_name` |
| Out of memory | `docker system prune -a` |
| Database connection | `docker-compose restart neo4j postgres` |
| SSL expired | `sudo certbot renew && sudo systemctl reload nginx` |
| Cache issues | `docker exec africgraph-redis redis-cli FLUSHALL` |
| Search not working | `curl -X POST http://localhost:8000/api/v1/search/index/all` |

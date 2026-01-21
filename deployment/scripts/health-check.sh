#!/bin/bash
# Health check script for AfricGraph services

set -e

COMPOSE_FILE="docker-compose.prod.yml"
HEALTHY=true

echo "Checking AfricGraph services health..."

# Check if docker-compose is running
if ! docker-compose -f ${COMPOSE_FILE} ps | grep -q "Up"; then
    echo "❌ Docker services are not running"
    HEALTHY=false
fi

# Check backend health
echo "Checking backend..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    HEALTHY=false
fi

# Check frontend
echo "Checking frontend..."
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    HEALTHY=false
fi

# Check databases
echo "Checking databases..."

# PostgreSQL
if docker exec africgraph-postgres pg_isready -U ${POSTGRES_USER:-africgraph} > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL health check failed"
    HEALTHY=false
fi

# Neo4j
if docker exec africgraph-neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD} "RETURN 1" > /dev/null 2>&1; then
    echo "✅ Neo4j is healthy"
else
    echo "❌ Neo4j health check failed"
    HEALTHY=false
fi

# Redis
if docker exec africgraph-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    HEALTHY=false
fi

# Elasticsearch
if curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch is healthy"
else
    echo "❌ Elasticsearch health check failed"
    HEALTHY=false
fi

if [ "${HEALTHY}" = true ]; then
    echo ""
    echo "✅ All services are healthy!"
    exit 0
else
    echo ""
    echo "❌ Some services are unhealthy!"
    exit 1
fi

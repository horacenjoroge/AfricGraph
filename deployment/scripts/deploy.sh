#!/bin/bash
# Deployment script for AfricGraph on VPS

set -e

ENV="${1:-production}"
COMPOSE_FILE="docker-compose.prod.yml"

echo "Deploying AfricGraph (${ENV})..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Pull latest code
echo "Pulling latest code..."
git pull origin main || git pull origin master

# Build and start services
echo "Building and starting services..."
docker-compose -f ${COMPOSE_FILE} build --no-cache
docker-compose -f ${COMPOSE_FILE} up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Run database migrations (if needed)
echo "Running database migrations..."
docker-compose -f ${COMPOSE_FILE} exec -T backend python -m alembic upgrade head || echo "No migrations to run"

# Warm up cache
echo "Warming up cache..."
docker-compose -f ${COMPOSE_FILE} exec -T backend python -c "
from src.cache.warming import warm_all
warm_all()
" || echo "Cache warming failed, continuing..."

# Show service status
echo "Service status:"
docker-compose -f ${COMPOSE_FILE} ps

echo "Deployment complete!"
echo "Check logs with: docker-compose -f ${COMPOSE_FILE} logs -f"

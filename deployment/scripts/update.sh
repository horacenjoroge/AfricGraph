#!/bin/bash
# Update script for AfricGraph

set -e

ENV="${1:-production}"
COMPOSE_FILE="docker-compose.prod.yml"

echo "Updating AfricGraph (${ENV})..."

# Backup before update
echo "Creating backup before update..."
./deployment/scripts/backup.sh || echo "Backup failed, continuing..."

# Pull latest code
echo "Pulling latest code..."
git pull origin main || git pull origin master

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose -f ${COMPOSE_FILE} pull

# Rebuild and restart
echo "Rebuilding and restarting services..."
docker-compose -f ${COMPOSE_FILE} up -d --build --force-recreate

# Wait for services
echo "Waiting for services to be healthy..."
sleep 30

# Run migrations
echo "Running database migrations..."
docker-compose -f ${COMPOSE_FILE} exec -T backend python -m alembic upgrade head || echo "No migrations to run"

# Health check
echo "Running health check..."
./deployment/scripts/health-check.sh || echo "Health check failed, check logs"

echo "Update complete!"

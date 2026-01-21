#!/bin/bash
# Rollback script for AfricGraph

set -e

BACKUP_FILE="${1}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Available backups:"
    ls -lh /var/backups/africgraph/*.tar.gz 2>/dev/null | tail -5 || echo "No backups found"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will rollback to a previous backup and may cause data loss!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "${confirm}" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo "Stopping services..."
docker-compose -f docker-compose.prod.yml down

echo "Restoring from backup..."
./deployment/scripts/restore-backup.sh "${BACKUP_FILE}"

echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for services..."
sleep 30

echo "Running health check..."
./deployment/scripts/health-check.sh || echo "Health check failed, check logs"

echo "Rollback complete!"

#!/bin/bash
# Enhanced restore script with validation

set -e

BACKUP_FILE="${1}"
BACKUP_TYPE="${2:-auto}"  # auto, neo4j, postgres, or all

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file> [backup_type]"
    echo ""
    echo "Backup types:"
    echo "  auto    - Auto-detect from filename (default)"
    echo "  neo4j   - Restore Neo4j only"
    echo "  postgres - Restore PostgreSQL only"
    echo "  all     - Restore both (if archive)"
    echo ""
    echo "Examples:"
    echo "  $0 /var/backups/africgraph/neo4j/neo4j_full_20240101_120000.dump.gz"
    echo "  $0 /var/backups/africgraph/postgres/postgres_20240101_120000.dump postgres"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will restore data from backup and may overwrite existing data!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "${confirm}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Test backup integrity first
echo "Testing backup integrity..."
./deployment/scripts/test-backup.sh "${BACKUP_FILE}"

if [ $? -ne 0 ]; then
    echo "ERROR: Backup test failed. Aborting restore."
    exit 1
fi

echo "Backup test passed. Proceeding with restore..."

# Determine backup type if auto
if [ "${BACKUP_TYPE}" = "auto" ]; then
    if [[ "${BACKUP_FILE}" == *"neo4j"* ]]; then
        BACKUP_TYPE="neo4j"
    elif [[ "${BACKUP_FILE}" == *"postgres"* ]]; then
        BACKUP_TYPE="postgres"
    else
        echo "Error: Cannot auto-detect backup type from filename"
        exit 1
    fi
fi

# Stop services that use databases
echo "Stopping services..."
docker-compose -f docker-compose.prod.yml stop backend celery || true

# Restore based on type
if [ "${BACKUP_TYPE}" = "neo4j" ] || [ "${BACKUP_TYPE}" = "all" ]; then
    echo "Restoring Neo4j..."
    
    # Decompress if needed
    if [[ "${BACKUP_FILE}" == *.gz ]]; then
        TEMP_FILE=$(mktemp)
        gunzip -c "${BACKUP_FILE}" > "${TEMP_FILE}"
        docker cp "${TEMP_FILE}" africgraph-neo4j:/tmp/neo4j.dump
        rm "${TEMP_FILE}"
    else
        docker cp "${BACKUP_FILE}" africgraph-neo4j:/tmp/neo4j.dump
    fi
    
    docker exec africgraph-neo4j neo4j-admin database load \
        --database=neo4j \
        --from-path=/tmp \
        --overwrite-destination=true
    
    docker exec africgraph-neo4j rm /tmp/neo4j.dump
    echo "Neo4j restore complete"
fi

if [ "${BACKUP_TYPE}" = "postgres" ] || [ "${BACKUP_TYPE}" = "all" ]; then
    echo "Restoring PostgreSQL..."
    
    # Drop and recreate database
    docker exec africgraph-postgres psql -U ${POSTGRES_USER:-africgraph} -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-africgraph};"
    docker exec africgraph-postgres psql -U ${POSTGRES_USER:-africgraph} -c "CREATE DATABASE ${POSTGRES_DB:-africgraph};"
    
    # Restore backup
    docker cp "${BACKUP_FILE}" africgraph-postgres:/tmp/postgres_backup.dump
    docker exec africgraph-postgres pg_restore \
        -U ${POSTGRES_USER:-africgraph} \
        -d ${POSTGRES_DB:-africgraph} \
        --clean \
        --if-exists \
        /tmp/postgres_backup.dump || \
    docker exec -i africgraph-postgres psql -U ${POSTGRES_USER:-africgraph} -d ${POSTGRES_DB:-africgraph} < "${BACKUP_FILE}"
    
    docker exec africgraph-postgres rm /tmp/postgres_backup.dump
    echo "PostgreSQL restore complete"
fi

# Restart services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml start backend celery

# Wait for services
echo "Waiting for services to be healthy..."
sleep 30

# Health check
echo "Running health check..."
./deployment/scripts/health-check.sh || echo "Health check failed, check logs"

echo "Restore complete!"

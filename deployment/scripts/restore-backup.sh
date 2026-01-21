#!/bin/bash
# Restore backup script for AfricGraph

set -e

BACKUP_FILE="${1}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/africgraph}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Available backups:"
    ls -lh ${BACKUP_DIR}/*.tar.gz 2>/dev/null || echo "No backups found"
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

echo "Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
POSTGRES_BACKUP=$(find "${TEMP_DIR}" -name "postgres_*.sql.gz" | head -1)
if [ -f "${POSTGRES_BACKUP}" ]; then
    gunzip -c "${POSTGRES_BACKUP}" | docker exec -i africgraph-postgres psql -U ${POSTGRES_USER:-africgraph} ${POSTGRES_DB:-africgraph}
    echo "PostgreSQL restored"
fi

# Restore Neo4j
echo "Restoring Neo4j..."
NEO4J_BACKUP=$(find "${TEMP_DIR}" -name "neo4j_*.dump" | head -1)
if [ -f "${NEO4J_BACKUP}" ]; then
    docker cp "${NEO4J_BACKUP}" africgraph-neo4j:/tmp/neo4j.dump
    docker exec africgraph-neo4j neo4j-admin database load --database=neo4j --from-path=/tmp --overwrite-destination=true
    docker exec africgraph-neo4j rm /tmp/neo4j.dump
    echo "Neo4j restored (restart required)"
fi

# Restore Redis (optional)
echo "Restoring Redis..."
REDIS_BACKUP=$(find "${TEMP_DIR}" -name "redis_*.rdb" | head -1)
if [ -f "${REDIS_BACKUP}" ]; then
    docker cp "${REDIS_BACKUP}" africgraph-redis:/data/dump.rdb
    docker restart africgraph-redis
    echo "Redis restored"
fi

# Cleanup
rm -rf "${TEMP_DIR}"

echo "Restore complete!"
echo "You may need to restart services: docker-compose -f docker-compose.prod.yml restart"

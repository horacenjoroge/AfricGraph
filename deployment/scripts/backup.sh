#!/bin/bash
# Backup script for AfricGraph data

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/africgraph}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-30}"

echo "Starting backup at $(date)"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec africgraph-postgres pg_dump -U ${POSTGRES_USER:-africgraph} ${POSTGRES_DB:-africgraph} | gzip > "${BACKUP_DIR}/postgres_${DATE}.sql.gz"

# Backup Neo4j
echo "Backing up Neo4j..."
docker exec africgraph-neo4j neo4j-admin database dump --database=neo4j --to-path=/tmp
docker cp africgraph-neo4j:/tmp/neo4j.dump "${BACKUP_DIR}/neo4j_${DATE}.dump"
docker exec africgraph-neo4j rm /tmp/neo4j.dump

# Backup Redis (optional - Redis is mostly cache)
echo "Backing up Redis..."
docker exec africgraph-redis redis-cli SAVE
docker cp africgraph-redis:/data/dump.rdb "${BACKUP_DIR}/redis_${DATE}.rdb" || echo "Redis backup skipped"

# Backup Elasticsearch
echo "Backing up Elasticsearch..."
docker exec africgraph-elasticsearch curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/tmp/backup"
  }
}' || echo "Snapshot repository may already exist"

docker exec africgraph-elasticsearch curl -X PUT "localhost:9200/_snapshot/backup/snapshot_${DATE}?wait_for_completion=true" || echo "Elasticsearch backup skipped"

# Create archive
echo "Creating backup archive..."
tar -czf "${BACKUP_DIR}/africgraph_backup_${DATE}.tar.gz" \
    "${BACKUP_DIR}/postgres_${DATE}.sql.gz" \
    "${BACKUP_DIR}/neo4j_${DATE}.dump" \
    "${BACKUP_DIR}/redis_${DATE}.rdb" 2>/dev/null || true

# Cleanup old backups
echo "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -type f -name "*.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -type f -name "*.dump" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -type f -name "*.rdb" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -type f -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup complete: ${BACKUP_DIR}/africgraph_backup_${DATE}.tar.gz"
echo "Backup finished at $(date)"

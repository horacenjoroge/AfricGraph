#!/bin/bash
# Enhanced backup script using Python orchestrator

set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/africgraph}"
BACKUP_TYPE="${1:-incremental}"  # full or incremental
CLOUD_PROVIDER="${CLOUD_PROVIDER:-}"  # s3, gcs, azure, or empty for local only

echo "Starting enhanced backup (${BACKUP_TYPE}) at $(date)"

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Run backup using Python orchestrator
cd /opt/africgraph || cd "$(dirname "$0")/../.."

python3 << EOF
import sys
import os
sys.path.insert(0, 'backend')

from src.backup.orchestrator import BackupOrchestrator, CloudProvider
from src.backup.retention import RetentionPolicy
from src.backup.testing import BackupTester

# Configure cloud storage if provider specified
cloud_provider = None
cloud_config = None

if "${CLOUD_PROVIDER}" == "s3":
    cloud_provider = CloudProvider.S3
    cloud_config = {
        "bucket": os.getenv("S3_BACKUP_BUCKET", "africgraph-backups"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
    }
elif "${CLOUD_PROVIDER}" == "gcs":
    cloud_provider = CloudProvider.GCS
    cloud_config = {
        "bucket": os.getenv("GCS_BACKUP_BUCKET", "africgraph-backups"),
        "project_id": os.getenv("GCP_PROJECT_ID"),
    }
elif "${CLOUD_PROVIDER}" == "azure":
    cloud_provider = CloudProvider.AZURE
    cloud_config = {
        "container": os.getenv("AZURE_BACKUP_CONTAINER", "africgraph-backups"),
        "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
    }

# Initialize orchestrator
orchestrator = BackupOrchestrator(
    backup_dir="${BACKUP_DIR}",
    neo4j_container="africgraph-neo4j",
    postgres_container="africgraph-postgres",
    cloud_provider=cloud_provider,
    cloud_config=cloud_config,
    retention_policy=RetentionPolicy(
        daily_retention=int(os.getenv("BACKUP_DAILY_RETENTION", "7")),
        weekly_retention=int(os.getenv("BACKUP_WEEKLY_RETENTION", "4")),
        monthly_retention=int(os.getenv("BACKUP_MONTHLY_RETENTION", "12")),
        yearly_retention=int(os.getenv("BACKUP_YEARLY_RETENTION", "5")),
    ),
)

# Run backup
if "${BACKUP_TYPE}" == "full":
    results = orchestrator.run_full_backup()
else:
    results = orchestrator.run_incremental_backup()

# Test backups
tester = BackupTester()
if results.get("neo4j"):
    neo4j_test = tester.test_neo4j_backup(results["neo4j"])
    if not all(neo4j_test.values()):
        print(f"WARNING: Neo4j backup test failed: {neo4j_test}", file=sys.stderr)
        sys.exit(1)

if results.get("postgres"):
    postgres_test = tester.test_postgres_backup(results["postgres"])
    if not all(postgres_test.values()):
        print(f"WARNING: PostgreSQL backup test failed: {postgres_test}", file=sys.stderr)
        sys.exit(1)

print(f"Backup completed successfully: {results}")
EOF

if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $(date)"
    exit 0
else
    echo "Backup failed at $(date)"
    exit 1
fi

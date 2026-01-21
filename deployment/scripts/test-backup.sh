#!/bin/bash
# Test backup integrity

set -e

BACKUP_FILE="${1}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /var/backups/africgraph/neo4j/neo4j_full_20240101_120000.dump.gz"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "Testing backup: ${BACKUP_FILE}"

cd /opt/africgraph || cd "$(dirname "$0")/../.."

python3 << EOF
import sys
sys.path.insert(0, 'backend')

from src.backup.testing import BackupTester

tester = BackupTester()

# Determine backup type from filename
if "neo4j" in "${BACKUP_FILE}":
    results = tester.test_neo4j_backup("${BACKUP_FILE}")
    print(f"Neo4j backup test results: {results}")
    if not all(results.values()):
        print("ERROR: Backup test failed!", file=sys.stderr)
        sys.exit(1)
elif "postgres" in "${BACKUP_FILE}":
    results = tester.test_postgres_backup("${BACKUP_FILE}")
    print(f"PostgreSQL backup test results: {results}")
    if not all(results.values()):
        print("ERROR: Backup test failed!", file=sys.stderr)
        sys.exit(1)
else:
    print("Unknown backup type", file=sys.stderr)
    sys.exit(1)

print("Backup test passed!")
EOF

if [ $? -eq 0 ]; then
    echo "✅ Backup test passed"
    exit 0
else
    echo "❌ Backup test failed"
    exit 1
fi

#!/bin/bash
# List available backups

BACKUP_DIR="${BACKUP_DIR:-/var/backups/africgraph}"

echo "Available Backups:"
echo "=================="
echo ""

cd /opt/africgraph || cd "$(dirname "$0")/../.."

python3 << EOF
import sys
sys.path.insert(0, 'backend')

from src.backup.orchestrator import BackupOrchestrator

orchestrator = BackupOrchestrator(backup_dir="${BACKUP_DIR}")
backups = orchestrator.list_backups()

print("Neo4j Backups:")
print("-" * 60)
if backups["neo4j"]:
    for backup in backups["neo4j"][:10]:  # Show latest 10
        print(f"  {backup['file']}")
        print(f"    Size: {backup['size']:,} bytes")
        print(f"    Created: {backup['created']}")
        print()
else:
    print("  No Neo4j backups found")
    print()

print("PostgreSQL Backups:")
print("-" * 60)
if backups["postgres"]:
    for backup in backups["postgres"][:10]:  # Show latest 10
        print(f"  {backup['file']}")
        print(f"    Size: {backup['size']:,} bytes")
        print(f"    Created: {backup['created']}")
        print()
else:
    print("  No PostgreSQL backups found")
    print()
EOF

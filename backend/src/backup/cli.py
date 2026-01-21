"""CLI tool for backup operations."""
import argparse
import sys
import os
from pathlib import Path

from src.backup.orchestrator import BackupOrchestrator, CloudProvider
from src.backup.retention import RetentionPolicy
from src.backup.testing import BackupTester
from src.infrastructure.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AfricGraph Backup CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Run backup")
    backup_parser.add_argument(
        "--type",
        choices=["full", "incremental"],
        default="incremental",
        help="Backup type",
    )
    backup_parser.add_argument(
        "--cloud",
        choices=["s3", "gcs", "azure"],
        help="Upload to cloud storage",
    )
    backup_parser.add_argument(
        "--backup-dir",
        default="/var/backups/africgraph",
        help="Backup directory",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test backup")
    test_parser.add_argument("backup_file", help="Path to backup file")

    # List command
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument(
        "--backup-dir",
        default="/var/backups/africgraph",
        help="Backup directory",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get backup status")
    status_parser.add_argument(
        "--backup-dir",
        default="/var/backups/africgraph",
        help="Backup directory",
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old backups")
    cleanup_parser.add_argument(
        "--backup-dir",
        default="/var/backups/africgraph",
        help="Backup directory",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Configure logging
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    try:
        if args.command == "backup":
            # Configure cloud storage
            cloud_provider = None
            cloud_config = None

            if args.cloud == "s3":
                cloud_provider = CloudProvider.S3
                cloud_config = {
                    "bucket": os.getenv("S3_BACKUP_BUCKET", "africgraph-backups"),
                    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "region": os.getenv("AWS_REGION", "us-east-1"),
                }
            elif args.cloud == "gcs":
                cloud_provider = CloudProvider.GCS
                cloud_config = {
                    "bucket": os.getenv("GCS_BACKUP_BUCKET", "africgraph-backups"),
                    "project_id": os.getenv("GCP_PROJECT_ID"),
                }
            elif args.cloud == "azure":
                cloud_provider = CloudProvider.AZURE
                cloud_config = {
                    "container": os.getenv("AZURE_BACKUP_CONTAINER", "africgraph-backups"),
                    "connection_string": os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
                }

            orchestrator = BackupOrchestrator(
                backup_dir=args.backup_dir,
                cloud_provider=cloud_provider,
                cloud_config=cloud_config,
            )

            if args.type == "full":
                results = orchestrator.run_full_backup()
            else:
                results = orchestrator.run_incremental_backup()

            print(f"Backup completed: {results}")
            sys.exit(0 if results.get("neo4j") or results.get("postgres") else 1)

        elif args.command == "test":
            tester = BackupTester()
            if "neo4j" in args.backup_file:
                results = tester.test_neo4j_backup(args.backup_file)
            elif "postgres" in args.backup_file:
                results = tester.test_postgres_backup(args.backup_file)
            else:
                print("Unknown backup type", file=sys.stderr)
                sys.exit(1)

            if all(results.values()):
                print("✅ Backup test passed")
                sys.exit(0)
            else:
                print(f"❌ Backup test failed: {results}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "list":
            orchestrator = BackupOrchestrator(backup_dir=args.backup_dir)
            backups = orchestrator.list_backups()
            print("Neo4j backups:")
            for backup in backups["neo4j"]:
                print(f"  - {backup['file']} ({backup['size']} bytes, {backup['created']})")
            print("\nPostgreSQL backups:")
            for backup in backups["postgres"]:
                print(f"  - {backup['file']} ({backup['size']} bytes, {backup['created']})")

        elif args.command == "status":
            orchestrator = BackupOrchestrator(backup_dir=args.backup_dir)
            status = orchestrator.get_backup_status()
            print(f"Neo4j: {status['neo4j']['count']} backups")
            if status["neo4j"]["latest"]:
                print(f"  Latest: {status['neo4j']['latest']['file']}")
            print(f"PostgreSQL: {status['postgres']['count']} backups")
            if status["postgres"]["latest"]:
                print(f"  Latest: {status['postgres']['latest']['file']}")
            print(f"Cloud enabled: {status['cloud_enabled']}")

        elif args.command == "cleanup":
            policy = RetentionPolicy()
            results = policy.cleanup(args.backup_dir)
            print(f"Cleanup completed: {results['deleted']} deleted, {results['kept']} kept")

    except Exception as e:
        logger.exception("Command failed", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

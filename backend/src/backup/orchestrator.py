"""Backup orchestrator coordinating all backup operations."""
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import os

from src.backup.neo4j_backup import Neo4jBackup, should_do_full_backup
from src.backup.postgres_backup import PostgresBackup
from src.backup.cloud_storage import CloudStorageBackup, CloudProvider
from src.backup.retention import RetentionPolicy
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BackupOrchestrator:
    """Orchestrates backup operations across all systems."""

    def __init__(
        self,
        backup_dir: str = "/var/backups/africgraph",
        neo4j_container: str = "africgraph-neo4j",
        postgres_container: str = "africgraph-postgres",
        neo4j_password: Optional[str] = None,
        postgres_password: Optional[str] = None,
        cloud_provider: Optional[CloudProvider] = None,
        cloud_config: Optional[dict] = None,
        retention_policy: Optional[RetentionPolicy] = None,
    ):
        """
        Initialize backup orchestrator.

        Args:
            backup_dir: Base backup directory
            neo4j_container: Neo4j container name
            postgres_container: PostgreSQL container name
            neo4j_password: Neo4j password
            postgres_password: PostgreSQL password
            cloud_provider: Cloud storage provider (optional)
            cloud_config: Cloud storage configuration
            retention_policy: Retention policy (optional)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.neo4j_backup = Neo4jBackup(
            neo4j_container=neo4j_container,
            backup_dir=str(self.backup_dir / "neo4j"),
        )
        self.postgres_backup = PostgresBackup(
            container=postgres_container,
            backup_dir=str(self.backup_dir / "postgres"),
        )

        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.postgres_password = postgres_password or os.getenv("POSTGRES_PASSWORD")

        self.cloud_storage = None
        if cloud_provider and cloud_config:
            self.cloud_storage = CloudStorageBackup(cloud_provider, cloud_config)

        self.retention_policy = retention_policy or RetentionPolicy()

    def run_full_backup(self) -> Dict[str, Optional[str]]:
        """
        Run a full backup of all systems.

        Returns:
            Dictionary with backup file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "neo4j": None,
            "postgres": None,
            "cloud_uploaded": False,
        }

        logger.info("Starting full backup", timestamp=timestamp)

        # Backup Neo4j
        try:
            results["neo4j"] = self.neo4j_backup.full_backup(self.neo4j_password)
        except Exception as e:
            logger.exception("Neo4j backup failed", error=str(e))

        # Backup PostgreSQL
        try:
            results["postgres"] = self.postgres_backup.backup(self.postgres_password)
        except Exception as e:
            logger.exception("PostgreSQL backup failed", error=str(e))

        # Upload to cloud if configured
        if self.cloud_storage:
            try:
                if results["neo4j"]:
                    remote_path = f"neo4j/neo4j_full_{timestamp}.dump.gz"
                    if self.cloud_storage.upload(results["neo4j"], remote_path):
                        results["cloud_uploaded"] = True

                if results["postgres"]:
                    remote_path = f"postgres/postgres_{timestamp}.dump"
                    if self.cloud_storage.upload(results["postgres"], remote_path):
                        results["cloud_uploaded"] = True
            except Exception as e:
                logger.exception("Cloud upload failed", error=str(e))

        # Apply retention policy
        try:
            self.retention_policy.cleanup(str(self.backup_dir))
        except Exception as e:
            logger.exception("Retention cleanup failed", error=str(e))

        logger.info("Full backup completed", results=results)
        return results

    def run_incremental_backup(self) -> Dict[str, Optional[str]]:
        """
        Run an incremental backup (Neo4j only, PostgreSQL uses full backups).

        Returns:
            Dictionary with backup file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "neo4j": None,
            "cloud_uploaded": False,
        }

        logger.info("Starting incremental backup", timestamp=timestamp)

        # Check if we should do full backup instead
        if should_do_full_backup(str(self.backup_dir / "neo4j")):
            logger.info("Switching to full backup (time threshold reached)")
            return self.run_full_backup()

        # Backup Neo4j incrementally
        try:
            latest_backup = self.neo4j_backup.get_latest_backup()
            results["neo4j"] = self.neo4j_backup.incremental_backup(
                self.neo4j_password, latest_backup
            )
        except Exception as e:
            logger.exception("Neo4j incremental backup failed", error=str(e))

        # Upload to cloud if configured
        if self.cloud_storage and results["neo4j"]:
            try:
                remote_path = f"neo4j/neo4j_incremental_{timestamp}.dump.gz"
                if self.cloud_storage.upload(results["neo4j"], remote_path):
                    results["cloud_uploaded"] = True
            except Exception as e:
                logger.exception("Cloud upload failed", error=str(e))

        logger.info("Incremental backup completed", results=results)
        return results

    def list_backups(self) -> Dict[str, List[Dict]]:
        """List all available backups."""
        return {
            "neo4j": self.neo4j_backup.list_backups(),
            "postgres": self.postgres_backup.list_backups(),
        }

    def get_backup_status(self) -> Dict:
        """Get backup status and statistics."""
        neo4j_backups = self.neo4j_backup.list_backups()
        postgres_backups = self.postgres_backup.list_backups()

        return {
            "neo4j": {
                "count": len(neo4j_backups),
                "latest": neo4j_backups[0] if neo4j_backups else None,
            },
            "postgres": {
                "count": len(postgres_backups),
                "latest": postgres_backups[0] if postgres_backups else None,
            },
            "cloud_enabled": self.cloud_storage is not None,
        }

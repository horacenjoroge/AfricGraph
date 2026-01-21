"""Neo4j backup utilities with incremental support."""
import subprocess
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

from src.infrastructure.logging import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class Neo4jBackup:
    """Neo4j backup manager with full and incremental backups."""

    def __init__(
        self,
        neo4j_container: str = "africgraph-neo4j",
        backup_dir: str = "/var/backups/africgraph/neo4j",
    ):
        """
        Initialize Neo4j backup manager.

        Args:
            neo4j_container: Docker container name
            backup_dir: Directory to store backups
        """
        self.neo4j_container = neo4j_container
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def full_backup(self, password: str) -> Optional[str]:
        """
        Create a full backup of Neo4j database.

        Returns:
            Path to backup file or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"neo4j_full_{timestamp}.dump"

        try:
            logger.info("Starting Neo4j full backup", backup_file=str(backup_file))

            # Create backup inside container
            cmd = [
                "docker",
                "exec",
                self.neo4j_container,
                "neo4j-admin",
                "database",
                "dump",
                "--database=neo4j",
                f"--to-path=/tmp/neo4j_backup_{timestamp}.dump",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Copy backup from container
            subprocess.run(
                [
                    "docker",
                    "cp",
                    f"{self.neo4j_container}:/tmp/neo4j_backup_{timestamp}.dump",
                    str(backup_file),
                ],
                check=True,
            )

            # Cleanup container temp file
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.neo4j_container,
                    "rm",
                    f"/tmp/neo4j_backup_{timestamp}.dump",
                ],
                check=False,
            )

            # Compress backup
            compressed_file = f"{backup_file}.gz"
            subprocess.run(["gzip", str(backup_file)], check=True)

            logger.info("Neo4j full backup completed", backup_file=compressed_file)
            return compressed_file

        except subprocess.CalledProcessError as e:
            logger.error("Neo4j backup failed", error=str(e), stderr=e.stderr)
            return None
        except Exception as e:
            logger.exception("Neo4j backup failed", error=str(e))
            return None

    def incremental_backup(self, password: str, last_backup: Optional[str] = None) -> Optional[str]:
        """
        Create an incremental backup of Neo4j database.

        Args:
            password: Neo4j password
            last_backup: Path to last backup file for incremental

        Returns:
            Path to backup file or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"neo4j_incremental_{timestamp}.dump"

        try:
            logger.info("Starting Neo4j incremental backup", backup_file=str(backup_file))

            # For incremental backup, we use the same dump command
            # Neo4j 5.x supports incremental backups via transaction logs
            # This is a simplified version - in production, use neo4j-backup tool
            cmd = [
                "docker",
                "exec",
                self.neo4j_container,
                "neo4j-admin",
                "database",
                "dump",
                "--database=neo4j",
                f"--to-path=/tmp/neo4j_backup_{timestamp}.dump",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Copy backup from container
            subprocess.run(
                [
                    "docker",
                    "cp",
                    f"{self.neo4j_container}:/tmp/neo4j_backup_{timestamp}.dump",
                    str(backup_file),
                ],
                check=True,
            )

            # Cleanup
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.neo4j_container,
                    "rm",
                    f"/tmp/neo4j_backup_{timestamp}.dump",
                ],
                check=False,
            )

            # Compress
            compressed_file = f"{backup_file}.gz"
            subprocess.run(["gzip", str(backup_file)], check=True)

            logger.info("Neo4j incremental backup completed", backup_file=compressed_file)
            return compressed_file

        except subprocess.CalledProcessError as e:
            logger.error("Neo4j incremental backup failed", error=str(e))
            return None
        except Exception as e:
            logger.exception("Neo4j incremental backup failed", error=str(e))
            return None

    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups."""
        backups = []
        for backup_file in self.backup_dir.glob("*.dump.gz"):
            stat = backup_file.stat()
            backups.append({
                "file": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def get_latest_backup(self) -> Optional[str]:
        """Get the latest backup file path."""
        backups = self.list_backups()
        return backups[0]["file"] if backups else None


def should_do_full_backup(backup_dir: str, days_between_full: int = 7) -> bool:
    """
    Determine if a full backup should be performed.

    Args:
        backup_dir: Backup directory
        days_between_full: Days between full backups

    Returns:
        True if full backup should be done
    """
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    # Find latest full backup
    full_backups = list(backup_path.glob("neo4j_full_*.dump.gz"))
    if not full_backups:
        return True

    latest_full = max(full_backups, key=lambda p: p.stat().st_mtime)
    age_days = (datetime.now() - datetime.fromtimestamp(latest_full.stat().st_mtime)).days

    return age_days >= days_between_full

"""PostgreSQL backup utilities."""
import subprocess
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PostgresBackup:
    """PostgreSQL backup manager."""

    def __init__(
        self,
        container: str = "africgraph-postgres",
        db_name: str = "africgraph",
        db_user: str = "africgraph",
        backup_dir: str = "/var/backups/africgraph/postgres",
    ):
        """
        Initialize PostgreSQL backup manager.

        Args:
            container: Docker container name
            db_name: Database name
            db_user: Database user
            backup_dir: Directory to store backups
        """
        self.container = container
        self.db_name = db_name
        self.db_user = db_user
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, password: Optional[str] = None) -> Optional[str]:
        """
        Create a PostgreSQL backup.

        Args:
            password: Database password (optional, can use .pgpass)

        Returns:
            Path to backup file or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"postgres_{timestamp}.sql"

        try:
            logger.info("Starting PostgreSQL backup", backup_file=str(backup_file))

            # Set password via environment if provided
            env = {}
            if password:
                env["PGPASSWORD"] = password

            # Create backup
            cmd = [
                "docker",
                "exec",
                self.container,
                "pg_dump",
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-F",
                "c",  # Custom format (compressed)
                "-f",
                f"/tmp/postgres_backup_{timestamp}.dump",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)

            # Copy backup from container
            subprocess.run(
                [
                    "docker",
                    "cp",
                    f"{self.container}:/tmp/postgres_backup_{timestamp}.dump",
                    str(backup_file),
                ],
                check=True,
            )

            # Cleanup container temp file
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.container,
                    "rm",
                    f"/tmp/postgres_backup_{timestamp}.dump",
                ],
                check=False,
            )

            logger.info("PostgreSQL backup completed", backup_file=str(backup_file))
            return str(backup_file)

        except subprocess.CalledProcessError as e:
            logger.error("PostgreSQL backup failed", error=str(e), stderr=e.stderr)
            return None
        except Exception as e:
            logger.exception("PostgreSQL backup failed", error=str(e))
            return None

    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups."""
        backups = []
        for backup_file in self.backup_dir.glob("*.dump"):
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

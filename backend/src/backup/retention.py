"""Backup retention policy management."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import os

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RetentionPolicy:
    """Backup retention policy manager."""

    def __init__(
        self,
        daily_retention: int = 7,
        weekly_retention: int = 4,
        monthly_retention: int = 12,
        yearly_retention: int = 5,
    ):
        """
        Initialize retention policy.

        Args:
            daily_retention: Number of daily backups to keep
            weekly_retention: Number of weekly backups to keep
            monthly_retention: Number of monthly backups to keep
            yearly_retention: Number of yearly backups to keep
        """
        self.daily_retention = daily_retention
        self.weekly_retention = weekly_retention
        self.monthly_retention = monthly_retention
        self.yearly_retention = yearly_retention

    def classify_backup(self, backup_path: Path) -> str:
        """
        Classify backup as daily, weekly, monthly, or yearly.

        Args:
            backup_path: Path to backup file

        Returns:
            Classification: 'daily', 'weekly', 'monthly', or 'yearly'
        """
        stat = backup_path.stat()
        backup_time = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()

        age_days = (now - backup_time).days

        if age_days < 7:
            return "daily"
        elif age_days < 30:
            return "weekly"
        elif age_days < 365:
            return "monthly"
        else:
            return "yearly"

    def should_keep(self, backup_path: Path, all_backups: List[Path]) -> bool:
        """
        Determine if backup should be kept based on retention policy.

        Args:
            backup_path: Path to backup file
            all_backups: List of all backup files

        Returns:
            True if backup should be kept
        """
        classification = self.classify_backup(backup_path)

        if classification == "daily":
            # Keep most recent N daily backups
            daily_backups = [
                b for b in all_backups
                if self.classify_backup(b) == "daily"
            ]
            daily_backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return backup_path in daily_backups[:self.daily_retention]

        elif classification == "weekly":
            # Keep most recent N weekly backups (one per week)
            weekly_backups = [
                b for b in all_backups
                if self.classify_backup(b) == "weekly"
            ]
            # Group by week
            weekly_groups = {}
            for backup in weekly_backups:
                backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
                week_key = f"{backup_time.year}-W{backup_time.isocalendar()[1]}"
                if week_key not in weekly_groups:
                    weekly_groups[week_key] = []
                weekly_groups[week_key].append(backup)

            # Keep latest backup from each week
            keep_backups = []
            for week_backups in weekly_groups.values():
                keep_backups.append(max(week_backups, key=lambda p: p.stat().st_mtime))

            return backup_path in keep_backups[:self.weekly_retention]

        elif classification == "monthly":
            # Keep most recent N monthly backups (one per month)
            monthly_backups = [
                b for b in all_backups
                if self.classify_backup(b) == "monthly"
            ]
            # Group by month
            monthly_groups = {}
            for backup in monthly_backups:
                backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
                month_key = f"{backup_time.year}-{backup_time.month:02d}"
                if month_key not in monthly_groups:
                    monthly_groups[month_key] = []
                monthly_groups[month_key].append(backup)

            # Keep latest backup from each month
            keep_backups = []
            for month_backups in monthly_groups.values():
                keep_backups.append(max(month_backups, key=lambda p: p.stat().st_mtime))

            return backup_path in keep_backups[:self.monthly_retention]

        else:  # yearly
            # Keep most recent N yearly backups (one per year)
            yearly_backups = [
                b for b in all_backups
                if self.classify_backup(b) == "yearly"
            ]
            # Group by year
            yearly_groups = {}
            for backup in yearly_backups:
                backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
                year_key = str(backup_time.year)
                if year_key not in yearly_groups:
                    yearly_groups[year_key] = []
                yearly_groups[year_key].append(backup)

            # Keep latest backup from each year
            keep_backups = []
            for year_backups in yearly_groups.values():
                keep_backups.append(max(year_backups, key=lambda p: p.stat().st_mtime))

            return backup_path in keep_backups[:self.yearly_retention]

    def cleanup(self, backup_dir: str) -> Dict[str, int]:
        """
        Clean up old backups based on retention policy.

        Args:
            backup_dir: Directory containing backups

        Returns:
            Dictionary with cleanup statistics
        """
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return {"deleted": 0, "kept": 0}

        all_backups = list(backup_path.glob("*"))
        deleted = 0
        kept = 0

        for backup in all_backups:
            if backup.is_file():
                if self.should_keep(backup, all_backups):
                    kept += 1
                else:
                    try:
                        backup.unlink()
                        deleted += 1
                        logger.info("Deleted old backup", file=str(backup))
                    except Exception as e:
                        logger.error("Failed to delete backup", file=str(backup), error=str(e))

        logger.info("Backup cleanup completed", deleted=deleted, kept=kept)
        return {"deleted": deleted, "kept": kept}

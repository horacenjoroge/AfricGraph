"""Backup management API endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel

from src.backup.orchestrator import BackupOrchestrator, CloudProvider
from src.backup.retention import RetentionPolicy
from src.backup.testing import BackupTester
from src.infrastructure.logging import get_logger
from src.config.settings import settings

router = APIRouter(prefix="/backup", tags=["backup"])
logger = get_logger(__name__)


class BackupRequest(BaseModel):
    """Backup request model."""
    backup_type: str = "incremental"  # full or incremental
    cloud_upload: bool = False


class BackupResponse(BaseModel):
    """Backup response model."""
    success: bool
    timestamp: str
    neo4j_backup: Optional[str] = None
    postgres_backup: Optional[str] = None
    cloud_uploaded: bool = False
    message: str


@router.post("/run", response_model=BackupResponse)
def run_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
) -> BackupResponse:
    """
    Trigger a backup operation.

    Can run in background for long-running operations.
    """
    try:
        # Configure cloud storage if enabled
        cloud_provider = None
        cloud_config = None

        if request.cloud_upload:
            # Get cloud provider from settings
            provider = getattr(settings, "backup_cloud_provider", None)
            if provider == "s3":
                cloud_provider = CloudProvider.S3
                cloud_config = {
                    "bucket": getattr(settings, "backup_s3_bucket", "africgraph-backups"),
                    "aws_access_key_id": getattr(settings, "backup_aws_access_key", None),
                    "aws_secret_access_key": getattr(settings, "backup_aws_secret_key", None),
                    "region": getattr(settings, "backup_aws_region", "us-east-1"),
                }
            elif provider == "gcs":
                cloud_provider = CloudProvider.GCS
                cloud_config = {
                    "bucket": getattr(settings, "backup_gcs_bucket", "africgraph-backups"),
                    "project_id": getattr(settings, "backup_gcp_project", None),
                }

        # Initialize orchestrator
        orchestrator = BackupOrchestrator(
            backup_dir=getattr(settings, "backup_dir", "/var/backups/africgraph"),
            neo4j_container="africgraph-neo4j",
            postgres_container="africgraph-postgres",
            cloud_provider=cloud_provider,
            cloud_config=cloud_config,
            retention_policy=RetentionPolicy(),
        )

        # Run backup
        if request.backup_type == "full":
            results = orchestrator.run_full_backup()
        else:
            results = orchestrator.run_incremental_backup()

        return BackupResponse(
            success=True,
            timestamp=results.get("timestamp", ""),
            neo4j_backup=results.get("neo4j"),
            postgres_backup=results.get("postgres"),
            cloud_uploaded=results.get("cloud_uploaded", False),
            message="Backup completed successfully",
        )

    except Exception as e:
        logger.exception("Backup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/status")
def get_backup_status() -> Dict:
    """Get backup status and statistics."""
    try:
        orchestrator = BackupOrchestrator(
            backup_dir=getattr(settings, "backup_dir", "/var/backups/africgraph"),
        )
        return orchestrator.get_backup_status()
    except Exception as e:
        logger.exception("Failed to get backup status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/list")
def list_backups() -> Dict[str, List[Dict]]:
    """List all available backups."""
    try:
        orchestrator = BackupOrchestrator(
            backup_dir=getattr(settings, "backup_dir", "/var/backups/africgraph"),
        )
        return orchestrator.list_backups()
    except Exception as e:
        logger.exception("Failed to list backups", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/test/{backup_file:path}")
def test_backup(backup_file: str) -> Dict[str, bool]:
    """
    Test backup file integrity.

    Args:
        backup_file: Path to backup file (relative to backup directory)
    """
    try:
        backup_path = f"/var/backups/africgraph/{backup_file}"
        tester = BackupTester()

        if "neo4j" in backup_file:
            results = tester.test_neo4j_backup(backup_path)
        elif "postgres" in backup_file:
            results = tester.test_postgres_backup(backup_path)
        else:
            raise HTTPException(status_code=400, detail="Unknown backup type")

        return results

    except Exception as e:
        logger.exception("Backup test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/cleanup")
def cleanup_backups() -> Dict[str, int]:
    """Run retention policy cleanup."""
    try:
        policy = RetentionPolicy()
        results = policy.cleanup(getattr(settings, "backup_dir", "/var/backups/africgraph"))
        return results
    except Exception as e:
        logger.exception("Cleanup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

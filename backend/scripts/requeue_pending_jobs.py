#!/usr/bin/env python3
"""Re-queue pending ingestion jobs that were never processed."""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pipeline.job_store import get_job, update_job_status, STATUS_PENDING
from src.ingestion.pipeline.tasks import ingest_mobile_money, ingest_accounting
from src.infrastructure.database.postgres_client import postgres_client
from sqlalchemy import text

TABLE = "ingestion_jobs"
STATUS_PENDING = "pending"


def get_pending_jobs():
    """Get all pending jobs from the database."""
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"""
            SELECT id, source, source_params, status
            FROM {TABLE} 
            WHERE status = :status
            ORDER BY created_at DESC
            """),
            {"status": STATUS_PENDING},
        )
        return [dict(row._mapping) for row in r.fetchall()]


def fix_path_for_container(path: str) -> str:
    """Convert absolute host path to container-relative path."""
    # If path is absolute and contains /backend/uploads, convert to relative
    if path.startswith("/") and "/backend/uploads" in path:
        # Extract just the filename part
        filename = Path(path).name
        return f"uploads/{filename}"
    # If already relative or in uploads, return as is
    if path.startswith("uploads/"):
        return path
    # If absolute but not in expected location, try to extract filename
    return f"uploads/{Path(path).name}"


def requeue_jobs():
    """Re-queue all pending jobs."""
    jobs = get_pending_jobs()
    
    if not jobs:
        print("No pending jobs found.")
        return
    
    print(f"Found {len(jobs)} pending job(s). Re-queuing...")
    
    for job in jobs:
        job_id = str(job["id"])
        source = job["source"]
        source_params = job["source_params"] or {}
        
        print(f"\nProcessing job {job_id} (source: {source})")
        
        try:
            if source == "mobile_money":
                path = source_params.get("path", "")
                provider = source_params.get("provider", "mpesa")
                currency = source_params.get("currency", "KES")
                
                # Fix path for container
                fixed_path = fix_path_for_container(path)
                print(f"  Original path: {path}")
                print(f"  Fixed path: {fixed_path}")
                
                # Re-queue the task
                ingest_mobile_money.delay(fixed_path, provider, currency, job_id=job_id)
                print(f"  ✓ Task queued successfully")
                
            elif source == "accounting":
                connector = source_params.get("connector", "")
                tenant_id = source_params.get("tenant_id")
                modified_after = source_params.get("modified_after")
                
                # Re-queue the task
                ingest_accounting.delay(
                    connector,
                    tenant_id=tenant_id,
                    modified_after=modified_after,
                    job_id=job_id,
                )
                print(f"  ✓ Task queued successfully")
            else:
                print(f"  ✗ Unknown source type: {source}")
                
        except Exception as e:
            print(f"  ✗ Failed to queue task: {e}")
    
    print(f"\n✓ Re-queued {len(jobs)} job(s)")


if __name__ == "__main__":
    # Ensure database connection
    from src.infrastructure.database.postgres_client import postgres_client
    postgres_client.connect()
    
    requeue_jobs()

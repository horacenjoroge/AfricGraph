"""Manual trigger API for ingestion and job status."""
from typing import Any, Optional
from pathlib import Path
from datetime import datetime
import shutil
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field

from src.ingestion.pipeline.job_store import create_job, get_job, list_jobs
from src.ingestion.pipeline.tasks import ingest_accounting, ingest_mobile_money

router = APIRouter(prefix="", tags=["ingestion"])


class MobileMoneyTrigger(BaseModel):
    path: str = Field(..., description="Server-accessible path to CSV")
    provider: str = Field("mpesa", description="mpesa or airtel")
    currency: str = Field("KES", description="Default currency")


class AccountingTrigger(BaseModel):
    connector: str = Field(..., description="xero, quickbooks, or odoo")
    tenant_id: Optional[str] = Field(None, description="Required for xero/quickbooks")
    modified_after: Optional[str] = Field(None, description="ISO datetime for incremental sync")


@router.post("/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)) -> dict:
    """Upload a CSV file and return the server path."""
    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}_{file.filename}"
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path for Docker compatibility
        return {
            "file_path": str(file_path),  # Relative path, not absolute
            "filename": file.filename,
            "file_id": file_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


def _normalize_path(path: str) -> str:
    """Convert absolute path to relative path for Docker compatibility."""
    path_obj = Path(path)
    # If it's an absolute path, try to make it relative
    if path_obj.is_absolute():
        # Check if it's in the backend/uploads directory
        if "uploads" in path_obj.parts:
            # Extract the uploads/... part
            uploads_idx = path_obj.parts.index("uploads")
            return str(Path(*path_obj.parts[uploads_idx:]))
        # Otherwise, just use the filename in uploads/
        return f"uploads/{path_obj.name}"
    # Already relative, return as-is
    return path


@router.post("/mobile-money")
def trigger_mobile_money(body: MobileMoneyTrigger) -> dict:
    """Enqueue mobile money ingestion. Returns job_id to poll status."""
    from src.tenancy.context import get_current_tenant
    
    # Get tenant from current context (set by middleware)
    tenant = get_current_tenant()
    tenant_id = tenant.tenant_id if tenant else None
    
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Tenant context required for ingestion. Please set X-Tenant-ID header or select a tenant."
        )
    
    # Normalize path to be relative for Docker
    normalized_path = _normalize_path(body.path)
    jid = create_job("mobile_money", {
        "path": normalized_path,
        "provider": body.provider,
        "currency": body.currency,
        "tenant_id": tenant_id
    })
    ingest_mobile_money.delay(normalized_path, body.provider, body.currency, job_id=jid, tenant_id=tenant_id)
    return {"job_id": jid, "status": "pending"}


@router.post("/accounting")
def trigger_accounting(body: AccountingTrigger) -> dict:
    """Enqueue accounting ingestion. Returns job_id to poll status."""
    jid = create_job(
        "accounting",
        {"connector": body.connector, "tenant_id": body.tenant_id, "modified_after": body.modified_after},
    )
    ingest_accounting.delay(
        body.connector,
        tenant_id=body.tenant_id,
        modified_after=body.modified_after,
        job_id=jid,
    )
    return {"job_id": jid, "status": "pending"}


@router.get("/jobs")
def list_ingestion_jobs(
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
) -> dict:
    """List all ingestion jobs, optionally filtered by status."""
    jobs = list_jobs(limit=limit, status=status)
    return {
        "jobs": jobs,
        "total": len(jobs),
    }


@router.get("/jobs/{job_id}")
def get_ingestion_job(job_id: str) -> dict:
    """Return ingestion job status, stats, and error_message if failed."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    # Convert to match frontend expected format
    return {
        "job_id": str(job["id"]),
        "job_type": job["source"],
        "status": job["status"],
        "created_at": job["created_at"].isoformat() if isinstance(job["created_at"], datetime) else str(job["created_at"]),
        "started_at": job["started_at"].isoformat() if job["started_at"] and isinstance(job["started_at"], datetime) else (job["started_at"] if job["started_at"] else None),
        "completed_at": job["finished_at"].isoformat() if job["finished_at"] and isinstance(job["finished_at"], datetime) else (job["finished_at"] if job["finished_at"] else None),
        "error_message": job["error_message"],
        "stats": job["stats"],
    }

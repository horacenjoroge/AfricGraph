"""Manual trigger API for ingestion and job status."""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.ingestion.pipeline.job_store import create_job, get_job
from src.ingestion.pipeline.tasks import ingest_accounting, ingest_mobile_money

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class MobileMoneyTrigger(BaseModel):
    path: str = Field(..., description="Server-accessible path to CSV")
    provider: str = Field("mpesa", description="mpesa or airtel")
    currency: str = Field("KES", description="Default currency")


class AccountingTrigger(BaseModel):
    connector: str = Field(..., description="xero, quickbooks, or odoo")
    tenant_id: Optional[str] = Field(None, description="Required for xero/quickbooks")
    modified_after: Optional[str] = Field(None, description="ISO datetime for incremental sync")


@router.post("/mobile-money")
def trigger_mobile_money(body: MobileMoneyTrigger) -> dict:
    """Enqueue mobile money ingestion. Returns job_id to poll status."""
    jid = create_job("mobile_money", {"path": body.path, "provider": body.provider, "currency": body.currency})
    ingest_mobile_money.delay(body.path, body.provider, body.currency, job_id=jid)
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


@router.get("/jobs/{job_id}")
def get_ingestion_job(job_id: str) -> dict:
    """Return ingestion job status, stats, and error_message if failed."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

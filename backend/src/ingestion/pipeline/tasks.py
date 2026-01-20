"""Celery tasks for the ingestion pipeline: mobile money, accounting; DLQ; Beat schedule."""
from datetime import datetime
from typing import Any, Dict, Optional

from celery import Celery
from celery.schedules import crontab

from src.config.settings import settings
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client

# Broker: prefer celery_broker_url, else build from rabbitmq
_vhost = (getattr(settings, "rabbitmq_vhost", None) or "/").strip().strip("/")
_broker = settings.celery_broker_url or (
    f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
    f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}/{_vhost}"
)

app = Celery("ingestion", broker=_broker)
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_serializer = "json"
app.conf.timezone = "UTC"
app.conf.enable_utc = True
# Retries and DLQ: on_failure sets status=dlq in DB
# Beat
app.conf.beat_schedule = {
    "scheduled-mobile-money": {
        "task": "src.ingestion.pipeline.tasks.scheduled_mobile_money",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6h
    },
    "scheduled-accounting": {
        "task": "src.ingestion.pipeline.tasks.scheduled_accounting",
        "schedule": crontab(minute=30, hour="*/6"),
    },
}


def _ensure_connections() -> None:
    if not postgres_client.health_check():
        postgres_client.connect()
    if not neo4j_client.health_check():
        neo4j_client.connect()


def _on_failure_set_dlq(self, exc, task_id, args, kwargs, einfo):  # noqa: B902
    job_id = kwargs.get("job_id")
    if job_id:
        try:
            from .job_store import update_job_status, STATUS_DLQ

            _ensure_connections()
            update_job_status(job_id, STATUS_DLQ, error_message=str(exc)[:2000])
        except Exception:
            pass


def _build_accounting_connector(connector: str, tenant_id: Optional[str] = None):
    from src.integrations.accounting import (
        OdooConnector,
        QuickBooksConnector,
        XeroConnector,
        get_default_token_store,
    )

    c = (connector or "").lower()
    if c == "odoo":
        return OdooConnector()
    if c == "xero":
        return XeroConnector(token_store=get_default_token_store(), tenant_id=tenant_id or "")
    if c == "quickbooks":
        return QuickBooksConnector(token_store=get_default_token_store(), tenant_id=tenant_id or "")
    raise ValueError(f"unknown connector: {connector}. use xero, quickbooks, odoo")


@app.task(bind=True, autoretry_for=(Exception,), retries=3, on_failure=_on_failure_set_dlq)
def ingest_mobile_money(
    self,
    path: str,
    provider: str,
    currency: str = "KES",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pipeline: Parser (mobile_money.run) -> Normalizer -> Validator -> Graph Writer.
    job_id: optional; if provided, status is updated on this job. If not, a new job is created.
    """
    from .graph_writer import write_mobile_money
    from .job_store import STATUS_FAILED, STATUS_RUNNING, STATUS_SUCCESS, create_job, update_job_status
    from .validator import validate_canonical_transaction

    from src.ingestion.mobile_money.pipeline import run as mm_run
    from src.ingestion.normalizers import MobileMoneyNormalizer

    _ensure_connections()
    jid = job_id
    if not jid:
        jid = create_job("mobile_money", {"path": path, "provider": provider, "currency": currency})

    try:
        update_job_status(jid, STATUS_RUNNING)
        valid, invalid = mm_run(path, provider=provider, default_currency=currency or "KES")
        norm = MobileMoneyNormalizer()
        canonical = norm.normalize_many(valid)
        passed = []
        for t in canonical:
            errs = validate_canonical_transaction(t)
            if not errs:
                passed.append(t)
        write_mobile_money(passed)
        update_job_status(
            jid, STATUS_SUCCESS,
            stats={"rows_ok": len(passed), "rows_invalid": len(invalid) + (len(canonical) - len(passed))},
        )
        return {"job_id": jid, "rows_ok": len(passed), "rows_invalid": len(invalid)}
    except Exception as e:
        update_job_status(jid, STATUS_FAILED, error_message=str(e)[:2000])
        raise


@app.task(bind=True, autoretry_for=(Exception,), retries=3, on_failure=_on_failure_set_dlq)
def ingest_accounting(
    self,
    connector: str,
    tenant_id: Optional[str] = None,
    modified_after: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Pipeline: Connector (fetch) -> Normalizer -> Entity resolution (contacts) -> Validator -> Graph Writer.
    modified_after: ISO datetime string or None.
    """
    from .graph_writer import write_accounting
    from .job_store import STATUS_FAILED, STATUS_RUNNING, STATUS_SUCCESS, create_job, update_job_status
    from .validator import validate_canonical_contact, validate_canonical_invoice, validate_canonical_payment

    from src.ingestion.normalizers import AccountingNormalizer
    from src.ingestion.resolvers import resolve_entities

    _ensure_connections()
    jid = job_id
    if not job_id:
        jid = create_job("accounting", {"connector": connector, "tenant_id": tenant_id, "modified_after": modified_after})

    try:
        update_job_status(jid, STATUS_RUNNING)
        conn = _build_accounting_connector(connector, tenant_id)
        mod_dt = None
        if modified_after:
            try:
                mod_dt = datetime.fromisoformat(modified_after.replace("Z", "+00:00"))
            except Exception:
                pass
        contacts = conn.fetch_contacts(modified_after=mod_dt)
        invoices = conn.fetch_invoices(modified_after=mod_dt)
        payments = conn.fetch_payments(modified_after=mod_dt)
        norm = AccountingNormalizer()
        cc = norm.normalize_contacts(contacts)
        ci = norm.normalize_invoices(invoices)
        cp = norm.normalize_payments(payments)
        cc = resolve_entities(cc)
        c_ok = [c for c in cc if not validate_canonical_contact(c)]
        i_ok = [i for i in ci if not validate_canonical_invoice(i)]
        p_ok = [p for p in cp if not validate_canonical_payment(p)]
        write_accounting(c_ok, i_ok, p_ok)
        update_job_status(
            jid, STATUS_SUCCESS,
            stats={"contacts": len(c_ok), "invoices": len(i_ok), "payments": len(p_ok)},
        )
        return {"job_id": jid, "contacts": len(c_ok), "invoices": len(i_ok), "payments": len(p_ok)}
    except Exception as e:
        update_job_status(jid, STATUS_FAILED, error_message=str(e)[:2000])
        raise


@app.task
def scheduled_mobile_money() -> Optional[Dict[str, Any]]:
    """Beat: run ingest_mobile_money if ingestion_mobile_money_path is set."""
    from .job_store import create_job

    path = getattr(settings, "ingestion_mobile_money_path", None) or ""
    if not path.strip():
        return None
    provider = getattr(settings, "ingestion_mobile_money_provider", "mpesa") or "mpesa"
    _ensure_connections()
    jid = create_job("mobile_money", {"path": path, "provider": provider, "scheduled": True})
    ingest_mobile_money.delay(path, provider, "KES", job_id=jid)
    return {"job_id": jid, "scheduled": True}


@app.task
def scheduled_accounting() -> Optional[Dict[str, Any]]:
    """Beat: run ingest_accounting if ingestion_accounting_connector is set."""
    connector = getattr(settings, "ingestion_accounting_connector", None) or ""
    if not connector.strip():
        return None
    tenant = getattr(settings, "ingestion_accounting_tenant_id", None) or ""
    from .job_store import create_job

    _ensure_connections()
    jid = create_job("accounting", {"connector": connector, "tenant_id": tenant, "scheduled": True})
    ingest_accounting.delay(connector, tenant_id=tenant or None, job_id=jid)
    return {"job_id": jid, "scheduled": True}


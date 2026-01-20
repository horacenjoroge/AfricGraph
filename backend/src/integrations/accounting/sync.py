"""Incremental sync and conflict resolution."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseAccountingConnector
from .models import ConflictResolution, ExternalContact, ExternalInvoice, ExternalPayment


def run_sync(
    connector: BaseAccountingConnector,
    modified_after: Optional[datetime] = None,
    conflict: ConflictResolution = ConflictResolution.REMOTE_WINS,
    local_contacts: Optional[Dict[str, datetime]] = None,
    local_invoices: Optional[Dict[str, datetime]] = None,
    local_payments: Optional[Dict[str, datetime]] = None,
) -> Dict[str, Any]:
    """
    Incremental sync: fetch contacts, invoices, payments from connector since modified_after.
    local_*: optional maps of external_id -> updated_at for conflict. If not provided, all remote are accepted.
    conflict: REMOTE_WINS (accept all), LOCAL_WINS (skip if local exists), NEWEST_WINS (compare updated_at), MANUAL (append to conflicts).
    Returns: {contacts, invoices, payments, conflicts: [{entity, external_id, strategy}]}.
    """
    conflicts: List[Dict[str, Any]] = []

    def _filter_newest(
        items: List,
        local: Optional[Dict[str, datetime]],
        entity: str,
        get_id,
        get_updated,
    ) -> List:
        out = []
        for it in items:
            eid = get_id(it)
            loc_dt = (local or {}).get(eid) if local else None
            rem_dt = get_updated(it)
            if conflict == ConflictResolution.REMOTE_WINS or not local:
                out.append(it)
                continue
            if conflict == ConflictResolution.LOCAL_WINS and loc_dt:
                continue
            if conflict == ConflictResolution.NEWEST_WINS and loc_dt and rem_dt:
                rem_ts = rem_dt.timestamp() if hasattr(rem_dt, "timestamp") else 0
                loc_ts = loc_dt.timestamp() if hasattr(loc_dt, "timestamp") else 0
                if rem_ts <= loc_ts:
                    continue
            if conflict == ConflictResolution.MANUAL and loc_dt and rem_dt:
                conflicts.append({"entity": entity, "external_id": eid, "strategy": "manual"})
                continue
            out.append(it)
        return out

    raw_contacts = connector.fetch_contacts(modified_after)
    raw_invoices = connector.fetch_invoices(modified_after)
    raw_payments = connector.fetch_payments(modified_after)

    contacts = _filter_newest(
        raw_contacts,
        local_contacts,
        "contact",
        lambda c: c.external_id,
        lambda c: c.updated_at,
    )
    invoices = _filter_newest(
        raw_invoices,
        local_invoices,
        "invoice",
        lambda i: i.external_id,
        lambda i: i.updated_at,
    )
    payments = _filter_newest(
        raw_payments,
        local_payments,
        "payment",
        lambda p: p.external_id,
        lambda p: p.updated_at,
    )

    return {
        "contacts": contacts,
        "invoices": invoices,
        "payments": payments,
        "conflicts": conflicts,
    }

"""Entity extraction, relationship mapping, and graph upsert. Writes to Neo4j and audit log."""
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.config.settings import settings
from src.infrastructure.audit import audit_logger
from src.infrastructure.database.neo4j_client import neo4j_client
from src.cache.invalidation import invalidate_graph_cache

from src.ingestion.normalizers.canonical import (
    CanonicalContact,
    CanonicalInvoice,
    CanonicalPayment,
    CanonicalTransaction,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _person_id_from_txn(
    counterparty: Optional[str],
    counterparty_phone: Optional[str],
    resolved_id: Optional[str],
) -> str:
    if resolved_id and str(resolved_id).strip():
        return str(resolved_id).strip()
    raw = f"mm:{(counterparty or '')}:{(counterparty_phone or '')}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:20]
    return f"person:mm:{h}"


def _to_node_props(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if v is None:
            continue
        out[k] = v
    return out


def write_mobile_money(
    transactions: List[CanonicalTransaction],
    default_business_id: Optional[str] = None,
) -> Dict[str, int]:
    """
    Upsert Transaction and Person nodes, (Transaction)-[:INVOLVES]->(Person).
    Returns {nodes_merged, relationships_merged}.
    """
    bid = (default_business_id or getattr(settings, "default_business_id", None) or "default").strip()
    nodes, rels = 0, 0

    for t in transactions:
        tid = (t.source_id or "").strip()
        if not tid:
            continue
        
        # Extract provider_txn_id from source_id (format: "provider:id")
        provider_txn_id = None
        if ":" in tid:
            provider_txn_id = tid.split(":", 1)[1]
        
        # Get direction from raw data or infer from type
        direction = None
        if hasattr(t, 'raw') and isinstance(t.raw, dict) and t.raw.get('direction'):
            direction = t.raw['direction']
        elif t.type == "payment_in":
            direction = "from"  # received from
        elif t.type == "payment_out":
            direction = "to"  # sent to
        
        tx_props = _to_node_props({
            "id": tid,
            "amount": float(t.amount_original),  # Original KES amount
            "currency": (t.currency_original or "KES").strip(),  # Original currency
            "date": t.date.isoformat() if hasattr(t.date, "isoformat") else str(t.date),
            "type": (t.type or "payment_in").strip(),
            "direction": direction,  # "from" or "to"
            "description": (t.description or "")[:500],
            "source_provider": (t.source_provider or "").strip(),
            "provider_txn_id": provider_txn_id,  # Receipt number
            "counterparty_name": t.counterparty,  # Counterparty name
            "counterparty_phone": t.counterparty_phone,  # Phone number
            "balance_after": float(t.balance_after) if t.balance_after is not None else None,  # Balance after transaction
            "created_at": _now().isoformat(),
        })
        neo4j_client.merge_node("Transaction", tid, tx_props)
        nodes += 1

        person_id = _person_id_from_txn(t.counterparty, t.counterparty_phone, t.resolved_counterparty_entity_id)
        
        # Determine person name: prefer counterparty name, fallback to formatted phone or "Unknown"
        person_name = t.counterparty
        if not person_name or (person_name and any(c.isdigit() for c in person_name) and len([c for c in person_name if c.isdigit()]) >= 9):
            # Name is missing or is a phone number - use formatted phone or "Unknown"
            if t.counterparty_phone:
                person_name = f"Phone: {t.counterparty_phone}"
            else:
                person_name = "Unknown"
        
        person_props = _to_node_props({
            "id": person_id,
            "name": person_name.strip()[:255],
            "phone": t.counterparty_phone,  # Add phone
            "created_at": _now().isoformat(),
        })
        neo4j_client.merge_node("Person", person_id, person_props)
        nodes += 1

        neo4j_client.merge_relationship_by_business_id(
            "Transaction", tid, "Person", person_id, "INVOLVES", {
                "role": "counterparty",
                "direction": direction  # Add direction to relationship
            }
        )
        rels += 1

    if transactions:
        audit_logger.log_system("ingestion.mobile_money.write", extra={"count": len(transactions), "nodes": nodes, "rels": rels})
        # Invalidate graph cache for all affected nodes to ensure fresh data is shown
        invalidate_graph_cache()  # Clear all graph caches since we don't know which specific nodes were affected
    
    return {"nodes_merged": nodes, "relationships_merged": rels}


def write_accounting(
    contacts: List[CanonicalContact],
    invoices: List[CanonicalInvoice],
    payments: List[CanonicalPayment],
    default_business_id: Optional[str] = None,
) -> Dict[str, int]:
    """
    Upsert Customer, Invoice, Payment; Business-ISSUED-Invoice; Payment-SETTLES-Invoice.
    Ensures Business node when default_business_id is set.
    """
    bid = (default_business_id or getattr(settings, "default_business_id", None) or "default").strip()
    nodes, rels = 0, 0

    if bid:
        neo4j_client.merge_node("Business", bid, _to_node_props({
            "id": bid, "name": "Default", "created_at": _now().isoformat(),
        }))
        nodes += 1

    for c in contacts:
        cid = (c.resolved_entity_id or c.source_id or "").strip()
        if not cid:
            continue
        neo4j_client.merge_node("Customer", cid, _to_node_props({
            "id": cid, "name": (c.name or "").strip()[:255], "created_at": _now().isoformat(),
        }))
        nodes += 1

    for i in invoices:
        iid = (i.source_id or "").strip()
        if not iid:
            continue
        neo4j_client.merge_node("Invoice", iid, _to_node_props({
            "id": iid,
            "number": (i.number or "").strip(),
            "amount": float(i.amount),
            "currency": (i.currency or "USD").strip(),
            "issue_date": i.issue_date.isoformat() if hasattr(i.issue_date, "isoformat") else str(i.issue_date),
            "status": (i.status or "DRAFT").strip(),
            "created_at": _now().isoformat(),
        }))
        nodes += 1
        if bid:
            neo4j_client.merge_relationship_by_business_id("Business", bid, "Invoice", iid, "ISSUED", {})
            rels += 1

    for p in payments:
        pid = (p.source_id or "").strip()
        if not pid:
            continue
        neo4j_client.merge_node("Payment", pid, _to_node_props({
            "id": pid,
            "amount": float(p.amount),
            "currency": (p.currency or "USD").strip(),
            "date": p.date.isoformat() if hasattr(p.date, "isoformat") else str(p.date),
            "created_at": _now().isoformat(),
        }))
        nodes += 1
        inv_id = (getattr(p, "invoice_source_id", None) or getattr(p, "resolved_invoice_entity_id", None) or "").strip()
        if inv_id:
            neo4j_client.merge_relationship_by_business_id("Payment", pid, "Invoice", inv_id, "SETTLES", {})
            rels += 1

    total = len(contacts) + len(invoices) + len(payments)
    if total > 0:
        audit_logger.log_system("ingestion.accounting.write", extra={"contacts": len(contacts), "invoices": len(invoices), "payments": len(payments), "nodes": nodes, "rels": rels})
    return {"nodes_merged": nodes, "relationships_merged": rels}

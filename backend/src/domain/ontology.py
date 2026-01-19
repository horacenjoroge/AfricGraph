"""
Ontology schema definitions for the AfricGraph knowledge graph.

Defines node labels, relationship types, required properties,
uniqueness constraints, and relationship cardinality rules.
"""

from typing import Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Node labels (entity types)
# ---------------------------------------------------------------------------

NODE_LABELS: Set[str] = {
    "Business",
    "Person",
    "Transaction",
    "Invoice",
    "Payment",
    "Supplier",
    "Customer",
    "Product",
    "BankAccount",
    "Loan",
    "Asset",
    "Location",
}

# ---------------------------------------------------------------------------
# Relationship types
# ---------------------------------------------------------------------------

RELATIONSHIP_TYPES: Set[str] = {
    "OWNS",
    "DIRECTOR_OF",
    "BUYS_FROM",
    "SELLS_TO",
    "ISSUED",
    "SETTLES",
    "INVOLVES",
    "HOLDS_ACCOUNT",
    "GRANTED_TO",
}

# ---------------------------------------------------------------------------
# Required properties per node label
# ---------------------------------------------------------------------------

NODE_REQUIRED_PROPERTIES: Dict[str, List[str]] = {
    "Business": ["id", "name", "created_at"],
    "Person": ["id", "name", "created_at"],
    "Transaction": ["id", "amount", "currency", "date", "created_at"],
    "Invoice": ["id", "number", "amount", "currency", "issue_date", "status", "created_at"],
    "Payment": ["id", "amount", "currency", "date", "created_at"],
    "Supplier": ["id", "name", "created_at"],
    "Customer": ["id", "name", "created_at"],
    "Product": ["id", "name", "created_at"],
    "BankAccount": ["id", "account_number", "bank_name", "currency", "created_at"],
    "Loan": ["id", "principal", "currency", "start_date", "status", "created_at"],
    "Asset": ["id", "name", "type", "created_at"],
    "Location": ["id", "address", "country", "created_at"],
}

# ---------------------------------------------------------------------------
# Uniqueness constraints: (label, property) -> one unique value per graph
# ---------------------------------------------------------------------------

UNIQUENESS_CONSTRAINTS: List[Tuple[str, str]] = [
    ("Business", "id"),
    ("Person", "id"),
    ("Transaction", "id"),
    ("Invoice", "id"),
    ("Payment", "id"),
    ("Supplier", "id"),
    ("Customer", "id"),
    ("Product", "id"),
    ("BankAccount", "id"),
    ("Loan", "id"),
    ("Asset", "id"),
    ("Location", "id"),
]

# ---------------------------------------------------------------------------
# Relationship cardinality rules
# (from_label, relationship_type, to_label) -> (from_card, to_card)
# from_card / to_card: "one" or "many"
# ---------------------------------------------------------------------------

CARDINALITY_ONE = "one"
CARDINALITY_MANY = "many"

RELATIONSHIP_CARDINALITY: List[Tuple[str, str, str, str, str]] = [
    # (from_label, type, to_label, from_side_card, to_side_card)
    ("Person", "OWNS", "Asset", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Business", "OWNS", "Asset", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Person", "OWNS", "Business", CARDINALITY_MANY, CARDINALITY_MANY),
    ("Person", "DIRECTOR_OF", "Business", CARDINALITY_MANY, CARDINALITY_MANY),
    ("Business", "BUYS_FROM", "Supplier", CARDINALITY_MANY, CARDINALITY_MANY),
    ("Business", "SELLS_TO", "Customer", CARDINALITY_MANY, CARDINALITY_MANY),
    ("Supplier", "ISSUED", "Invoice", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Business", "ISSUED", "Invoice", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Payment", "SETTLES", "Invoice", CARDINALITY_ONE, CARDINALITY_MANY),
    ("Transaction", "INVOLVES", "Person", CARDINALITY_ONE, CARDINALITY_MANY),
    ("Transaction", "INVOLVES", "Business", CARDINALITY_ONE, CARDINALITY_MANY),
    ("Transaction", "INVOLVES", "BankAccount", CARDINALITY_ONE, CARDINALITY_MANY),
    ("Person", "HOLDS_ACCOUNT", "BankAccount", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Business", "HOLDS_ACCOUNT", "BankAccount", CARDINALITY_MANY, CARDINALITY_ONE),
    ("Loan", "GRANTED_TO", "Person", CARDINALITY_ONE, CARDINALITY_MANY),
    ("Loan", "GRANTED_TO", "Business", CARDINALITY_ONE, CARDINALITY_ONE),
]

# ---------------------------------------------------------------------------
# Relationship properties: (from_label, type, to_label) -> {prop: data_type}
# Optional properties allowed on each relationship. Types: string, int, float, date, datetime, boolean.
# ---------------------------------------------------------------------------

RELATIONSHIP_PROPERTIES: Dict[Tuple[str, str, str], Dict[str, str]] = {
    ("Person", "OWNS", "Business"): {"percentage": "float", "since": "date"},
    ("Person", "OWNS", "Asset"): {"percentage": "float", "since": "date"},
    ("Business", "OWNS", "Asset"): {"percentage": "float", "since": "date"},
    ("Person", "DIRECTOR_OF", "Business"): {"role": "string", "since": "date"},
    ("Business", "BUYS_FROM", "Supplier"): {"since": "date"},
    ("Transaction", "INVOLVES", "Business"): {"role": "string"},
    ("Transaction", "INVOLVES", "Person"): {"role": "string"},
    ("Transaction", "INVOLVES", "BankAccount"): {"role": "string"},
}

# ---------------------------------------------------------------------------
# Data types for validation. Allowed: string, int, float, date, datetime, boolean.
# ---------------------------------------------------------------------------

DATA_TYPES: Set[str] = {"string", "int", "float", "date", "datetime", "boolean"}

# ---------------------------------------------------------------------------
# Node property data types: label -> {property: data_type}
# ---------------------------------------------------------------------------

NODE_PROPERTY_TYPES: Dict[str, Dict[str, str]] = {
    "Business": {"id": "string", "name": "string", "created_at": "datetime"},
    "Person": {"id": "string", "name": "string", "created_at": "datetime"},
    "Transaction": {"id": "string", "amount": "float", "currency": "string", "date": "date", "created_at": "datetime"},
    "Invoice": {"id": "string", "number": "string", "amount": "float", "currency": "string", "issue_date": "date", "status": "string", "created_at": "datetime"},
    "Payment": {"id": "string", "amount": "float", "currency": "string", "date": "date", "created_at": "datetime"},
    "Supplier": {"id": "string", "name": "string", "created_at": "datetime"},
    "Customer": {"id": "string", "name": "string", "created_at": "datetime"},
    "Product": {"id": "string", "name": "string", "created_at": "datetime"},
    "BankAccount": {"id": "string", "account_number": "string", "bank_name": "string", "currency": "string", "created_at": "datetime"},
    "Loan": {"id": "string", "principal": "float", "currency": "string", "start_date": "date", "status": "string", "created_at": "datetime"},
    "Asset": {"id": "string", "name": "string", "type": "string", "created_at": "datetime"},
    "Location": {"id": "string", "address": "string", "country": "string", "created_at": "datetime"},
}

# ---------------------------------------------------------------------------
# From/to labels allowed per relationship type (for validation)
# ---------------------------------------------------------------------------

RELATIONSHIP_FROM_LABELS: Dict[str, Set[str]] = {
    "OWNS": {"Person", "Business"},
    "DIRECTOR_OF": {"Person"},
    "BUYS_FROM": {"Business"},
    "SELLS_TO": {"Business"},
    "ISSUED": {"Supplier", "Business"},
    "SETTLES": {"Payment"},
    "INVOLVES": {"Transaction"},
    "HOLDS_ACCOUNT": {"Person", "Business"},
    "GRANTED_TO": {"Loan"},
}

RELATIONSHIP_TO_LABELS: Dict[str, Set[str]] = {
    "OWNS": {"Asset", "Business"},
    "DIRECTOR_OF": {"Business"},
    "BUYS_FROM": {"Supplier"},
    "SELLS_TO": {"Customer"},
    "ISSUED": {"Invoice"},
    "SETTLES": {"Invoice"},
    "INVOLVES": {"Person", "Business", "BankAccount"},
    "HOLDS_ACCOUNT": {"BankAccount"},
    "GRANTED_TO": {"Person", "Business"},
}


def get_required_properties(label: str) -> List[str]:
    """Return the list of required property names for a node label."""
    return list(NODE_REQUIRED_PROPERTIES.get(label, []))


def get_uniqueness_constraints() -> List[Tuple[str, str]]:
    """Return all (label, property) pairs that must be unique."""
    return list(UNIQUENESS_CONSTRAINTS)


def get_cardinality_rules() -> List[Tuple[str, str, str, str, str]]:
    """Return all (from_label, type, to_label, from_card, to_card) rules."""
    return list(RELATIONSHIP_CARDINALITY)


def is_valid_relationship(from_label: str, rel_type: str, to_label: str) -> bool:
    """Check if a relationship (from_label)-[:rel_type]->(to_label) is allowed."""
    from_ok = from_label in RELATIONSHIP_FROM_LABELS.get(rel_type, set())
    to_ok = to_label in RELATIONSHIP_TO_LABELS.get(rel_type, set())
    return from_ok and to_ok


def get_relationship_properties(from_label: str, rel_type: str, to_label: str) -> Dict[str, str]:
    """Return allowed properties and their data types for a relationship. Empty dict if none defined."""
    return dict(RELATIONSHIP_PROPERTIES.get((from_label, rel_type, to_label), {}))


def get_node_property_type(label: str, prop: str) -> str:
    """Return the data type for a node property, or empty string if unknown."""
    return NODE_PROPERTY_TYPES.get(label, {}).get(prop, "")


def is_valid_data_type(data_type: str) -> bool:
    """Check if a data type is in the allowed set."""
    return data_type in DATA_TYPES

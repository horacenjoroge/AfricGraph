"""Test helper utilities."""
import json
from typing import Dict, Any


def create_test_business(business_id: str = "test-business-1") -> Dict[str, Any]:
    """Create test business data."""
    return {
        "id": business_id,
        "name": f"Test Business {business_id}",
        "registration_number": f"REG-{business_id}",
        "sector": "Technology",
        "founded_date": "2020-01-01",
        "country": "KE",
    }


def create_test_person(person_id: str = "test-person-1") -> Dict[str, Any]:
    """Create test person data."""
    return {
        "id": person_id,
        "name": f"Test Person {person_id}",
        "email": f"test{person_id}@example.com",
        "phone": "+254712345678",
    }


def create_test_transaction(transaction_id: str = "test-transaction-1") -> Dict[str, Any]:
    """Create test transaction data."""
    return {
        "id": transaction_id,
        "amount": 1000.00,
        "currency": "KES",
        "description": f"Test transaction {transaction_id}",
        "date": "2024-01-15T10:00:00Z",
        "type": "payment",
    }


def assert_valid_json_response(response, expected_status: int = 200):
    """Assert response is valid JSON with expected status."""
    assert response.status_code == expected_status
    try:
        return response.json()
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"


def assert_error_response(response, expected_status: int, error_type: str = None):
    """Assert error response."""
    assert response.status_code == expected_status
    if error_type:
        data = response.json()
        assert "detail" in data or "error" in data

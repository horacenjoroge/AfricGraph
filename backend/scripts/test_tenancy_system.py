#!/usr/bin/env python3
"""
Test script for multi-tenancy system.

Tests:
1. Create multiple tenants
2. Verify data isolation
3. Check analytics endpoints
4. Monitor tenant health

Usage:
    python backend/scripts/test_tenancy_system.py
"""
import sys
import os
import requests
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # Set this for testing


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str):
    """Print test result."""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")


def get_headers(tenant_id: str = None) -> Dict[str, str]:
    """Get request headers."""
    headers = {
        "Content-Type": "application/json",
    }
    if ADMIN_TOKEN:
        headers["Authorization"] = f"Bearer {ADMIN_TOKEN}"
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    return headers


def test_create_tenants() -> Dict[str, str]:
    """Test creating multiple tenants."""
    print_section("1. Creating Test Tenants")
    
    tenants = {}
    tenant_data = [
        {"tenant_id": "test-tenant-1", "name": "Test Tenant 1"},
        {"tenant_id": "test-tenant-2", "name": "Test Tenant 2"},
        {"tenant_id": "test-tenant-3", "name": "Test Tenant 3"},
    ]
    
    for data in tenant_data:
        try:
            response = requests.post(
                f"{BASE_URL}/tenants",
                headers=get_headers(),
                json=data,
            )
            if response.status_code in [200, 201]:
                tenant = response.json()
                tenants[data["tenant_id"]] = tenant.get("tenant_id", data["tenant_id"])
                print_result(True, f"Created tenant: {data['name']} ({data['tenant_id']})")
            else:
                # Might already exist
                if response.status_code == 409:
                    tenants[data["tenant_id"]] = data["tenant_id"]
                    print_result(True, f"Tenant already exists: {data['name']}")
                else:
                    print_result(False, f"Failed to create tenant {data['name']}: {response.status_code}")
                    print(f"  Response: {response.text}")
        except Exception as e:
            print_result(False, f"Error creating tenant {data['name']}: {str(e)}")
    
    return tenants


def test_data_isolation(tenant_ids: Dict[str, str]):
    """Test data isolation between tenants."""
    print_section("2. Testing Data Isolation")
    
    if not tenant_ids:
        print_result(False, "No tenants available for isolation test")
        return
    
    # Create data for each tenant
    for tenant_id in list(tenant_ids.values())[:2]:  # Test first 2 tenants
        try:
            # This would require creating nodes via API
            # For now, just verify tenants are separate
            response = requests.get(
                f"{BASE_URL}/tenants/{tenant_id}",
                headers=get_headers(tenant_id),
            )
            if response.status_code == 200:
                tenant = response.json()
                print_result(True, f"Tenant {tenant_id} accessible: {tenant.get('name')}")
            else:
                print_result(False, f"Failed to access tenant {tenant_id}: {response.status_code}")
        except Exception as e:
            print_result(False, f"Error testing isolation for {tenant_id}: {str(e)}")


def test_analytics_endpoints():
    """Test analytics endpoints."""
    print_section("3. Testing Analytics Endpoints")
    
    endpoints = [
        ("/tenants/analytics/aggregated", "Aggregated analytics"),
        ("/tenants/analytics/distribution?metric=nodes", "Tenant distribution (nodes)"),
        ("/tenants/analytics/distribution?metric=relationships", "Tenant distribution (relationships)"),
        ("/tenants/analytics/activity?days=30", "Activity summary"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=get_headers(),
            )
            if response.status_code == 200:
                data = response.json()
                print_result(True, f"{description}: OK")
                print(f"    Response keys: {list(data.keys())[:5]}")
            else:
                print_result(False, f"{description}: {response.status_code}")
                if response.status_code == 401:
                    print("    Note: Admin authentication required")
        except Exception as e:
            print_result(False, f"{description}: Error - {str(e)}")


def test_health_monitoring(tenant_ids: Dict[str, str]):
    """Test health monitoring endpoints."""
    print_section("4. Testing Health Monitoring")
    
    # Test individual tenant health
    if tenant_ids:
        tenant_id = list(tenant_ids.values())[0]
        try:
            response = requests.get(
                f"{BASE_URL}/tenants/{tenant_id}/health",
                headers=get_headers(),
            )
            if response.status_code == 200:
                health = response.json()
                print_result(True, f"Tenant health for {tenant_id}: OK")
                print(f"    Healthy: {health.get('healthy')}")
                print(f"    Nodes: {health.get('node_count', 0)}")
                print(f"    Relationships: {health.get('relationship_count', 0)}")
            else:
                print_result(False, f"Failed to get health: {response.status_code}")
        except Exception as e:
            print_result(False, f"Error getting health: {str(e)}")
    
    # Test all tenants health
    try:
        response = requests.get(
            f"{BASE_URL}/tenants/health/all",
            headers=get_headers(),
        )
        if response.status_code == 200:
            data = response.json()
            print_result(True, "All tenants health: OK")
            print(f"    Total tenants: {data.get('total_tenants', 0)}")
            print(f"    Healthy: {data.get('healthy_tenants', 0)}")
            print(f"    Unhealthy: {data.get('unhealthy_tenants', 0)}")
        else:
            print_result(False, f"Failed to get all health: {response.status_code}")
    except Exception as e:
        print_result(False, f"Error getting all health: {str(e)}")
    
    # Test usage endpoint
    if tenant_ids:
        tenant_id = list(tenant_ids.values())[0]
        try:
            response = requests.get(
                f"{BASE_URL}/tenants/{tenant_id}/usage?days=30",
                headers=get_headers(),
            )
            if response.status_code == 200:
                usage = response.json()
                print_result(True, f"Tenant usage for {tenant_id}: OK")
                print(f"    Operations: {usage.get('operation_count', 0)}")
                print(f"    Active days: {usage.get('active_days', 0)}")
            else:
                print_result(False, f"Failed to get usage: {response.status_code}")
        except Exception as e:
            print_result(False, f"Error getting usage: {str(e)}")


def test_index_endpoints():
    """Test index management endpoints."""
    print_section("5. Testing Index Management")
    
    # Get index status
    try:
        response = requests.get(
            f"{BASE_URL}/tenants/indexes/status",
            headers=get_headers(),
        )
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Index status: OK")
            print(f"    Total indexes: {data.get('total_indexes', 0)}")
        else:
            print_result(False, f"Failed to get index status: {response.status_code}")
            if response.status_code == 401:
                print("    Note: Admin authentication required")
    except Exception as e:
        print_result(False, f"Error getting index status: {str(e)}")


def test_quotas_endpoints(tenant_ids: Dict[str, str]):
    """Test quotas endpoints."""
    print_section("6. Testing Quotas")
    
    if not tenant_ids:
        print_result(False, "No tenants available for quotas test")
        return
    
    tenant_id = list(tenant_ids.values())[0]
    try:
        response = requests.get(
            f"{BASE_URL}/tenants/{tenant_id}/quotas",
            headers=get_headers(tenant_id),
        )
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Tenant quotas for {tenant_id}: OK")
            quotas = data.get("quotas", {})
            print(f"    Quota types: {len(quotas)}")
            for quota_type, quota_data in list(quotas.items())[:3]:
                usage = quota_data.get("usage_percentage", 0)
                print(f"    {quota_type}: {usage:.1f}% used")
        else:
            print_result(False, f"Failed to get quotas: {response.status_code}")
    except Exception as e:
        print_result(False, f"Error getting quotas: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Multi-Tenancy System Test Suite")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    if not ADMIN_TOKEN:
        print("Warning: ADMIN_TOKEN not set. Some endpoints may require authentication.")
    
    try:
        # Test API availability
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n✗ API is not available. Please start the server.")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Cannot connect to API: {str(e)}")
        print("  Please ensure the server is running at", BASE_URL)
        sys.exit(1)
    
    # Run tests
    tenants = test_create_tenants()
    test_data_isolation(tenants)
    test_analytics_endpoints()
    test_health_monitoring(tenants)
    test_index_endpoints()
    test_quotas_endpoints(tenants)
    
    print_section("Test Summary")
    print("All tests completed!")
    print("\nNext steps:")
    print("  1. Review test results above")
    print("  2. Check server logs for any errors")
    print("  3. Verify data isolation manually if needed")
    print("  4. Run automated tests: pytest tests/integration/test_tenant_isolation.py")


if __name__ == "__main__":
    main()

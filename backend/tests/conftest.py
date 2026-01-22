"""Pytest configuration and shared fixtures."""
import pytest
import os
from typing import Generator
from unittest.mock import Mock, patch

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["NEO4J_URI"] = os.getenv("TEST_NEO4J_URI", "bolt://localhost:7687")
os.environ["POSTGRES_HOST"] = os.getenv("TEST_POSTGRES_HOST", "localhost")
os.environ["REDIS_HOST"] = os.getenv("TEST_REDIS_HOST", "localhost")


@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture."""
    from src.config.settings import Settings
    
    return Settings(
        neo4j_uri=os.getenv("TEST_NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user="neo4j",
        neo4j_password="test_password",
        postgres_host=os.getenv("TEST_POSTGRES_HOST", "localhost"),
        postgres_db="test_africgraph",
        postgres_user="test_user",
        postgres_password="test_password",
        redis_host=os.getenv("TEST_REDIS_HOST", "localhost"),
        redis_port=6379,
        jwt_secret_key="test_secret_key_for_testing_only",
        log_level="DEBUG",
    )


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    mock = Mock()
    mock.execute_cypher.return_value = []
    mock.find_node.return_value = None
    mock.merge_node.return_value = "test_node_id"
    mock.create_relationship.return_value = "test_rel_id"
    return mock


@pytest.fixture
def mock_postgres_client():
    """Mock PostgreSQL client."""
    mock = Mock()
    mock.execute.return_value = []
    mock.fetch_one.return_value = None
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    mock = Mock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_elasticsearch_client():
    """Mock Elasticsearch client."""
    mock = Mock()
    mock.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}
    mock.index.return_value = {"result": "created"}
    return mock


@pytest.fixture
def sample_business_data():
    """Sample business data for testing."""
    return {
        "id": "business-123",
        "name": "Test Business Ltd",
        "registration_number": "REG123456",
        "sector": "Technology",
        "founded_date": "2020-01-01",
        "country": "KE",
    }


@pytest.fixture
def sample_person_data():
    """Sample person data for testing."""
    return {
        "id": "person-123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+254712345678",
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        "id": "transaction-123",
        "amount": 1000.00,
        "currency": "KES",
        "description": "Test transaction",
        "date": "2024-01-15T10:00:00Z",
        "type": "payment",
    }


@pytest.fixture
def admin_subject():
    """Admin subject attributes for ABAC testing."""
    from src.security.abac.attributes import SubjectAttributes
    
    return SubjectAttributes(
        user_id="admin-1",
        role="admin",
        business_ids=None,
        permissions=["*"],
    )


@pytest.fixture
def owner_subject():
    """Business owner subject attributes for ABAC testing."""
    from src.security.abac.attributes import SubjectAttributes
    
    return SubjectAttributes(
        user_id="owner-1",
        role="owner",
        business_ids=["business-123"],
        permissions=["read", "write"],
    )


@pytest.fixture
def analyst_subject():
    """Analyst subject attributes for ABAC testing."""
    from src.security.abac.attributes import SubjectAttributes
    
    return SubjectAttributes(
        user_id="analyst-1",
        role="analyst",
        business_ids=None,
        permissions=["read"],
    )


@pytest.fixture
def test_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    yield
    # Cleanup if needed

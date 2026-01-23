# Testing Guide

This directory contains comprehensive tests for AfricGraph.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual functions
├── integration/       # Integration tests for API and database
├── security/          # Security tests (OWASP Top 10)
├── e2e/              # End-to-end tests
├── load/             # Load testing (Locust)
└── utils/            # Test utilities and helpers
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# API tests
pytest -m api

# Security tests
pytest -m security

# E2E tests
pytest -m e2e

# Graph query tests
pytest -m graph

# ABAC tests
pytest -m abac

# Fraud detection tests
pytest -m fraud
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Test File

```bash
pytest tests/unit/test_risk_scoring.py
```

### Run Specific Test

```bash
pytest tests/unit/test_risk_scoring.py::TestFactorScore::test_factor_score_creation
```

## Test Configuration

### Environment Variables

Set these for testing:

```bash
export TEST_NEO4J_URI=bolt://localhost:7687
export TEST_POSTGRES_HOST=localhost
export TEST_REDIS_HOST=localhost
export TESTING=true
```

### Pytest Configuration

See `pytest.ini` for configuration:
- Coverage threshold: 85%
- Test markers for categorization
- Async test support

## Load Testing

### Run Locust Load Tests

```bash
# Start Locust web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Run headless
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 1000 -r 100 -t 60s
```

Parameters:
- `-u 1000`: 1000 concurrent users
- `-r 100`: Spawn rate (users per second)
- `-t 60s`: Test duration

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `test_client`: FastAPI test client
- `mock_neo4j_client`: Mock Neo4j client
- `mock_postgres_client`: Mock PostgreSQL client
- `sample_business_data`: Sample business data
- `admin_subject`: Admin ABAC subject
- `owner_subject`: Owner ABAC subject

### Seed Data Fixtures

The test suite includes fixtures that use the seed data script to populate the database:

#### `seeded_test_data` (session-scoped)
Comprehensive test data that runs once per test session. Creates:
- 20 sample businesses (BIZ001-BIZ020)
- 15 sample people (PERSON001-PERSON015)
- Ownership, supplier, and director relationships
- 50 business-to-business transactions
- 200 mobile money transactions (M-Pesa & Airtel)
- 100 invoices with payment relationships
- Complex business scenarios (groups, shared directors)

**Usage:**
```python
@pytest.mark.integration
def test_with_seeded_data(seeded_test_data):
    """Test using comprehensive seeded data."""
    business_ids = seeded_test_data["business_ids"]
    person_ids = seeded_test_data["person_ids"]
    # Use the IDs in your test
    assert len(business_ids) == 20
```

#### `minimal_test_data` (function-scoped)
Creates fresh minimal data for each test:
- 3 sample businesses
- 2 sample people
- Basic ownership relationships

Automatically cleans up after each test.

**Usage:**
```python
def test_with_fresh_data(minimal_test_data):
    """Test with fresh data for each run."""
    business_ids = minimal_test_data["business_ids"]
    # Data is cleaned up automatically after test
```

#### Helper Fixtures
- `sample_business_ids`: List of all seeded business IDs
- `sample_person_ids`: List of all seeded person IDs
- `sample_business_id`: Single business ID (first one)
- `sample_person_id`: Single person ID (first one)

**Usage:**
```python
def test_business_search(sample_business_id, test_client):
    """Test searching for a seeded business."""
    response = test_client.get(f"/api/v1/businesses/{sample_business_id}")
    assert response.status_code == 200
```

## Writing Tests

### Unit Test Example

```python
@pytest.mark.unit
def test_my_function():
    """Test my function."""
    result = my_function(input)
    assert result == expected
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.api
def test_api_endpoint(test_client):
    """Test API endpoint."""
    response = test_client.get("/api/v1/businesses/123")
    assert response.status_code == 200
```

### Mock Example

```python
@patch("src.module.function")
def test_with_mock(mock_function):
    """Test with mock."""
    mock_function.return_value = "mocked"
    result = my_code()
    assert result == "mocked"
```

## Coverage Goals

- **Overall Coverage**: 85%+
- **Critical Modules**: 90%+
  - Risk scoring
  - Fraud detection
  - ABAC
  - API endpoints

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main/master
- Scheduled nightly runs

See `.github/workflows/test.yml` for CI configuration.

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Mock External Dependencies**: Don't hit real databases in unit tests
5. **Test Edge Cases**: Include boundary conditions
6. **Fast Tests**: Unit tests should be fast (< 1s)
7. **Clear Assertions**: One assertion per test when possible

## Troubleshooting

### Tests Failing

1. Check test database connectivity
2. Verify environment variables
3. Check test data setup
4. Review test logs

### Coverage Below Threshold

1. Identify uncovered code
2. Add tests for missing coverage
3. Review coverage report: `htmlcov/index.html`

### Slow Tests

1. Use `pytest -m "not slow"` to skip slow tests
2. Use `pytest-xdist` for parallel execution
3. Optimize test setup/teardown

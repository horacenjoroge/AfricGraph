.PHONY: test test-unit test-integration test-api test-security test-e2e test-coverage test-load clean

# Test commands
test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-api:
	pytest -m api

test-security:
	pytest -m security

test-e2e:
	pytest -m e2e -v

test-graph:
	pytest -m graph

test-abac:
	pytest -m abac

test-fraud:
	pytest -m fraud

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=85

test-fast:
	pytest -m "not slow"

test-load:
	locust -f tests/load/locustfile.py --host=http://localhost:8000

test-load-headless:
	locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 1000 -r 100 -t 60s

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf coverage.xml

# Install dependencies
install:
	pip install -r requirements.txt

# Development setup
dev-setup: install
	pip install -r requirements.txt

# Run all checks
check: test-coverage
	@echo "All checks passed!"

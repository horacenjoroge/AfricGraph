#!/bin/bash
# Test runner script for AfricGraph

set -e

TEST_TYPE="${1:-all}"
COVERAGE="${2:-true}"

echo "Running tests: ${TEST_TYPE}"

# Set test environment
export TESTING=true
export LOG_LEVEL=WARNING

# Run tests based on type
case "${TEST_TYPE}" in
    unit)
        echo "Running unit tests..."
        pytest -m unit ${COVERAGE:+"--cov=src --cov-report=term-missing"}
        ;;
    integration)
        echo "Running integration tests..."
        pytest -m integration ${COVERAGE:+"--cov=src --cov-report=term-missing"}
        ;;
    api)
        echo "Running API tests..."
        pytest -m api ${COVERAGE:+"--cov=src --cov-report=term-missing"}
        ;;
    security)
        echo "Running security tests..."
        pytest -m security
        ;;
    e2e)
        echo "Running E2E tests..."
        pytest -m e2e -v
        ;;
    graph)
        echo "Running graph query tests..."
        pytest -m graph
        ;;
    abac)
        echo "Running ABAC tests..."
        pytest -m abac
        ;;
    fraud)
        echo "Running fraud detection tests..."
        pytest -m fraud
        ;;
    all)
        echo "Running all tests..."
        if [ "${COVERAGE}" = "true" ]; then
            pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=85
        else
            pytest
        fi
        ;;
    *)
        echo "Unknown test type: ${TEST_TYPE}"
        echo "Usage: $0 [unit|integration|api|security|e2e|graph|abac|fraud|all] [coverage]"
        exit 1
        ;;
esac

echo "Tests completed!"

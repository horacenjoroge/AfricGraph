#!/bin/bash
# View logs script for AfricGraph

SERVICE="${1:-}"
COMPOSE_FILE="docker-compose.prod.yml"

if [ -z "${SERVICE}" ]; then
    echo "Viewing logs for all services..."
    docker-compose -f ${COMPOSE_FILE} logs -f
else
    echo "Viewing logs for ${SERVICE}..."
    docker-compose -f ${COMPOSE_FILE} logs -f ${SERVICE}
fi

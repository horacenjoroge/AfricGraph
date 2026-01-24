# AfricGraph

Ontology-driven decision platform for SMEs. Backend (FastAPI), frontend (React), and supporting services run via Docker Compose.

## Prerequisites

- Docker and Docker Compose
- Git

## Setup

1. Clone the repository and enter the project directory.

2. Create `.env` from the example and set required variables:

   ```bash
   cp .env.example .env
   ```

   Required in `.env` for `docker-compose up`:

   | Variable           | Description              |
   |--------------------|--------------------------|
   | `NEO4J_PASSWORD`   | Neo4j auth password      |
   | `POSTGRES_PASSWORD`| PostgreSQL password      |
   | `RABBITMQ_PASSWORD`| RabbitMQ password        |
   | `JWT_SECRET_KEY`   | Secret for JWT signing   |

   Optional (with defaults): `POSTGRES_DB`, `POSTGRES_USER`, `RABBITMQ_USER`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`, `CORS_ORIGINS`, `LOG_LEVEL`, `REACT_APP_API_URL`.

## Run

Start all services:

```bash
docker-compose up -d
```

Backend API: `http://localhost:8000`  
Health: `http://localhost:8000/health`  
Frontend: `http://localhost:3000`  
Neo4j Browser: `http://localhost:7474`  
RabbitMQ management: `http://localhost:15672`

Run in the foreground (logs in terminal):

```bash
docker-compose up
```

Stop:

```bash
docker-compose down
```

## Services and ports

| Service        | Port(s)    |
|----------------|------------|
| Backend (API)  | 8000       |
| Frontend       | 3000       |
| Neo4j          | 7474, 7687 |
| PostgreSQL     | 5432       |
| Redis          | 6379       |
| RabbitMQ       | 5672, 15672|
| Elasticsearch| 9200       |

## Local development (backend)

With Python 3.11+, from `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ensure Neo4j, Postgres, Redis, RabbitMQ, and Elasticsearch are reachable (e.g. via `docker-compose up` for those services) and set `POSTGRES_HOST`, `NEO4J_URI`, etc. in `.env` for localhost if needed.

Run the API:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Start Celery worker (for ingestion jobs):

```bash
celery -A src.ingestion.pipeline.tasks worker --loglevel=info
```

**Note**: Ingestion jobs require Celery workers to process. Jobs will stay in "pending" status until a worker picks them up. See `docs/celery-workers.md` for details.

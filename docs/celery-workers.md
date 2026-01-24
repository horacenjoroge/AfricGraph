# Running Celery Workers for Ingestion Jobs

## Overview

Ingestion jobs (mobile money, accounting) are processed automatically by Celery workers. Jobs don't require manual approval - they are queued and processed asynchronously.

## How It Works

1. **Job Creation**: When you trigger an ingestion job via the API or Admin panel, a job is created with status `pending`
2. **Queue**: The job is queued in RabbitMQ
3. **Worker Processing**: A Celery worker picks up the job automatically
4. **Status Updates**: 
   - `pending` → `running` (when worker starts)
   - `running` → `success` or `failed` (when complete)

## Starting Celery Workers

### Option 1: Using Docker Compose (Recommended)

If using Docker Compose, the Celery worker is already configured:

```bash
# Start all services including Celery worker
docker-compose up -d

# Or start just the Celery service
docker-compose up -d celery
```

The Celery worker will automatically start and process jobs.

### Option 2: Manual Start (Local Development)

From the `backend/` directory:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start Celery worker
celery -A src.ingestion.pipeline.tasks worker --loglevel=info
```

### Option 3: With Concurrency

For better performance, run multiple worker processes:

```bash
celery -A src.ingestion.pipeline.tasks worker --loglevel=info --concurrency=4
```

## Checking Worker Status

### Check if Workers are Running

```bash
# Using Docker
docker-compose ps celery

# Or check logs
docker-compose logs -f celery
```

### Check RabbitMQ Queue

Visit RabbitMQ Management UI: `http://localhost:15672`

- Username: `africgraph` (or from `.env`)
- Password: (from `RABBITMQ_PASSWORD` in `.env`)

Check the "Queues" tab to see pending jobs.

## Troubleshooting

### Jobs Stay in "Pending" Status

**Problem**: Jobs remain in `pending` status and never process.

**Solutions**:
1. **Check if Celery worker is running**:
   ```bash
   docker-compose ps celery
   # Or
   ps aux | grep celery
   ```

2. **Check RabbitMQ is running**:
   ```bash
   docker-compose ps rabbitmq
   ```

3. **Check worker logs**:
   ```bash
   docker-compose logs -f celery
   # Or if running manually, check terminal output
   ```

4. **Restart Celery worker**:
   ```bash
   docker-compose restart celery
   ```

### Connection Errors

If you see connection errors in worker logs:

1. **Check environment variables**:
   - `RABBITMQ_HOST`
   - `RABBITMQ_USER`
   - `RABBITMQ_PASSWORD`
   - `NEO4J_URI`
   - `POSTGRES_HOST`

2. **Verify services are accessible**:
   ```bash
   # Test RabbitMQ
   docker-compose exec rabbitmq rabbitmqctl status
   
   # Test Neo4j
   curl http://localhost:7474
   
   # Test PostgreSQL
   docker-compose exec postgres psql -U africgraph -d africgraph -c "SELECT 1"
   ```

## Monitoring Jobs

### Via Workflows Page

1. Navigate to **Workflows** page in the frontend
2. Click on **Ingestion Jobs** tab
3. See all jobs with their current status

### Via API

```bash
# List all jobs
curl http://localhost:8000/api/v1/ingest/jobs

# Get specific job
curl http://localhost:8000/api/v1/ingest/jobs/{job_id}
```

## Celery Beat (Scheduled Jobs)

Celery Beat runs scheduled ingestion jobs. To start it:

```bash
celery -A src.ingestion.pipeline.tasks beat --loglevel=info
```

Or with Docker Compose, add a separate service:

```yaml
celery-beat:
  # ... same config as celery worker ...
  command: celery -A src.ingestion.pipeline.tasks beat --loglevel=info
```

## Production Deployment

For production, use:

```bash
celery -A src.ingestion.pipeline.tasks worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --time-limit=3600
```

This provides:
- 4 concurrent workers
- Auto-restart after 1000 tasks (memory management)
- 1 hour timeout per task

# AfricGraph Monitoring & Observability

This directory contains Prometheus metrics, Grafana dashboards, and alerting configurations for monitoring the AfricGraph platform.

## Components

### Prometheus Metrics

- **Location**: `backend/src/monitoring/metrics.py`
- **Endpoint**: `GET /metrics`
- **Metrics Collected**:
  - API request rate, latency, errors
  - Neo4j query time, connection pool
  - Cache hit rate
  - Ingestion job success/failure
  - Risk calculation time
  - Fraud alert rate
  - Workflow approval time
  - System resources (CPU, memory, disk)
  - Search query performance

### Grafana Dashboards

Located in `backend/monitoring/grafana/dashboards/`:

1. **System Health** (`system-health.json`)
   - API request rate and latency
   - Error rates
   - System resource usage (CPU, memory, disk)

2. **Business Metrics** (`business-metrics.json`)
   - Risk calculations
   - Fraud alerts
   - High-risk business counts

3. **Performance Metrics** (`performance.json`)
   - Neo4j query performance
   - Cache hit rates
   - Ingestion job metrics
   - Search query performance

4. **User Activity** (`user-activity.json`)
   - API usage by endpoint
   - Workflow approvals
   - Search queries

### Prometheus Alerts

Located in `backend/monitoring/prometheus/alerts.yml`:

- **High API Error Rate**: >10 errors/sec for 5 minutes
- **Slow Queries**: Neo4j queries >2s (p95) for 5 minutes
- **Slow API Responses**: API responses >5s (p95) for 5 minutes
- **High Risk Businesses**: >50 high-risk businesses for 10 minutes
- **High Fraud Alert Rate**: >5 critical fraud alerts/sec for 5 minutes
- **System Resource Alerts**: High CPU (>80%), memory (>8GB), disk (>50GB)
- **Low Cache Hit Rate**: <50% for 10 minutes
- **High Ingestion Failure Rate**: >2 failures/sec for 5 minutes
- **Service Down**: Service unavailable for >1 minute

## Setup

### 1. Start Prometheus

```bash
prometheus --config.file=backend/monitoring/prometheus/prometheus.yml
```

### 2. Import Grafana Dashboards

1. Open Grafana (typically at `http://localhost:3000`)
2. Go to Dashboards → Import
3. Upload JSON files from `backend/monitoring/grafana/dashboards/`

### 3. Configure Alertmanager

1. Set up Alertmanager to receive alerts from Prometheus
2. Configure notification channels (email, Slack, webhook)
3. Update `prometheus.yml` with Alertmanager target

## Metrics Instrumentation

Metrics are automatically collected via:

- **Middleware**: API request/response metrics
- **System Collector**: Background thread collecting CPU/memory/disk
- **Service Integration**: Risk, fraud, workflow, cache, Neo4j services

See `backend/src/monitoring/instrumentation.py` for helper functions to add metrics to custom code.

## Usage

### View Metrics

```bash
curl http://localhost:8000/metrics
```

### Query Prometheus

```promql
# API request rate
rate(api_requests_total[5m])

# Cache hit rate
rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])

# Risk calculation duration (p95)
histogram_quantile(0.95, rate(risk_calculation_duration_seconds_bucket[5m]))
```

## Custom Metrics

To add custom metrics:

1. Define metric in `backend/src/monitoring/metrics.py`
2. Use instrumentation helpers from `backend/src/monitoring/instrumentation.py`
3. Update Grafana dashboards if needed

Example:

```python
from src.monitoring.instrumentation import track_neo4j_query

with track_neo4j_query("custom_query"):
    # Your code here
    pass
```

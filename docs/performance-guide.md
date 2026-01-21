# Performance Guide

This guide covers performance optimization, monitoring, and tuning for AfricGraph.

## Performance Metrics

### Key Metrics

- **API Response Time**: Target < 200ms (p95)
- **Database Query Time**: Target < 100ms (p95)
- **Cache Hit Rate**: Target > 80%
- **Throughput**: Target > 1000 requests/second

### Monitoring

View metrics at `/metrics` endpoint or Grafana dashboards:
- Request rate and latency
- Database query performance
- Cache hit rates
- System resources

## Optimization Strategies

### Database Optimization

#### Neo4j

1. **Indexes**
   ```cypher
   CREATE INDEX business_id_index FOR (b:Business) ON (b.id)
   CREATE INDEX person_email_index FOR (p:Person) ON (p.email)
   ```

2. **Query Optimization**
   - Use specific labels
   - Limit relationship traversal depth
   - Use WHERE clauses early
   - Avoid cartesian products

3. **Connection Pooling**
   - Configure appropriate pool size
   - Monitor connection usage
   - Adjust based on load

#### PostgreSQL

1. **Indexes**
   ```sql
   CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
   CREATE INDEX idx_users_email ON users(email);
   ```

2. **Query Optimization**
   - Use EXPLAIN ANALYZE
   - Optimize slow queries
   - Use appropriate data types

3. **Connection Pooling**
   - Configure pool size
   - Monitor connections
   - Use connection pooling

### Caching Strategy

#### Cache Layers

1. **Application Cache** (Redis)
   - Graph query results (5-30 min TTL)
   - Risk scores (30 min TTL)
   - Permission decisions (1 hour TTL)

2. **HTTP Cache**
   - Static assets
   - API responses (where appropriate)

#### Cache Warming

Warm frequently accessed data:
```bash
curl -X POST http://localhost:8000/api/v1/cache/warm
```

### API Optimization

1. **Pagination**
   - Always paginate list endpoints
   - Use cursor-based pagination for large datasets

2. **Field Selection**
   - Return only needed fields
   - Use GraphQL for flexible queries

3. **Async Processing**
   - Use background jobs for heavy operations
   - Return job IDs for long-running tasks

### Frontend Optimization

1. **Code Splitting**
   - Lazy load routes
   - Split large components

2. **Asset Optimization**
   - Minify JavaScript/CSS
   - Optimize images
   - Use CDN for static assets

3. **Caching**
   - Cache API responses
   - Use service workers
   - Cache static assets

## Performance Tuning

### System Resources

#### Memory

- **Neo4j**: Allocate 50% of available RAM
- **PostgreSQL**: Allocate 25% of available RAM
- **Elasticsearch**: Allocate 50% of available RAM (max 32GB)
- **Redis**: Allocate based on cache size needs

#### CPU

- Monitor CPU usage
- Scale horizontally if needed
- Optimize CPU-intensive operations

#### Disk

- Use SSD for databases
- Monitor disk I/O
- Implement log rotation

### Database Tuning

#### Neo4j

```bash
# Increase heap memory
NEO4J_dbms_memory_heap_max__size=4G

# Increase page cache
NEO4J_dbms_memory_pagecache_size=2G
```

#### PostgreSQL

```sql
-- Increase shared buffers
shared_buffers = 256MB

-- Increase work memory
work_mem = 16MB
```

#### Redis

```bash
# Set max memory
CONFIG SET maxmemory 1gb
CONFIG SET maxmemory-policy allkeys-lru
```

### Application Tuning

#### Backend Workers

Increase workers for high load:
```bash
uvicorn src.api.main:app --workers 4
```

#### Celery Workers

Increase concurrency:
```bash
celery -A src.ingestion.pipeline.tasks worker --concurrency=8
```

## Load Testing

### Using Locust

```bash
# Start Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 1000 \
  -r 100 \
  -t 60s
```

### Performance Targets

- **1000 concurrent users**: < 200ms response time
- **5000 requests/second**: System stable
- **99.9% uptime**: High availability

## Monitoring Performance

### Key Metrics to Watch

1. **Response Times**
   - p50, p95, p99 percentiles
   - Track by endpoint

2. **Error Rates**
   - 4xx errors (client errors)
   - 5xx errors (server errors)

3. **Database Performance**
   - Query execution time
   - Connection pool usage
   - Slow query count

4. **Cache Performance**
   - Hit rate
   - Miss rate
   - Eviction rate

### Alerts

Configure alerts for:
- High response times (> 1s p95)
- High error rates (> 1%)
- Low cache hit rate (< 70%)
- High database query time (> 500ms)

## Troubleshooting Performance

### Slow API Responses

1. Check database queries
2. Review cache hit rate
3. Check system resources
4. Review slow query logs

### High Database Load

1. Optimize queries
2. Add indexes
3. Increase connection pool
4. Consider read replicas

### Low Cache Hit Rate

1. Review cache TTL
2. Check cache size
3. Warm frequently accessed data
4. Review eviction policy

## Best Practices

1. **Monitor Continuously**: Use Prometheus/Grafana
2. **Profile Regularly**: Identify bottlenecks
3. **Optimize Incrementally**: One optimization at a time
4. **Test Changes**: Load test after optimizations
5. **Document Changes**: Keep performance notes

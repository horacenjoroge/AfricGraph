# Operational Runbooks

This document provides step-by-step procedures for common operational tasks.

## Service Management

### Start All Services

```bash
cd /opt/africgraph
docker-compose -f docker-compose.prod.yml up -d
```

### Stop All Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart a Service

```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### View Service Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Or use script
./deployment/scripts/logs.sh backend
```

### Check Service Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

## Health Checks

### Application Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": {"status": "healthy"},
    "postgres": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "rabbitmq": {"status": "healthy"},
    "elasticsearch": {"status": "healthy"}
  }
}
```

### Automated Health Check

```bash
./deployment/scripts/health-check.sh
```

## Database Operations

### Neo4j

#### Access Neo4j Browser

```bash
# Open in browser
http://localhost:7474

# Or if remote
http://your-vps-ip:7474
```

#### Backup Neo4j

```bash
./deployment/scripts/backup-enhanced.sh full
```

#### Restore Neo4j

```bash
./deployment/scripts/restore-enhanced.sh /path/to/backup neo4j
```

#### Check Neo4j Status

```bash
docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
```

### PostgreSQL

#### Connect to PostgreSQL

```bash
docker exec -it africgraph-postgres psql -U africgraph -d africgraph
```

#### Backup PostgreSQL

```bash
docker exec africgraph-postgres pg_dump -U africgraph africgraph > backup.sql
```

#### Restore PostgreSQL

```bash
docker exec -i africgraph-postgres psql -U africgraph africgraph < backup.sql
```

#### Check PostgreSQL Status

```bash
docker exec africgraph-postgres pg_isready -U africgraph
```

## Cache Management

### Clear Redis Cache

```bash
docker exec africgraph-redis redis-cli FLUSHALL
```

### Check Cache Statistics

```bash
docker exec africgraph-redis redis-cli INFO stats
```

### Warm Cache

```bash
curl -X POST http://localhost:8000/api/v1/cache/warm
```

## Search Operations

### Reindex Elasticsearch

```bash
curl -X POST http://localhost:8000/api/v1/search/index/all
```

### Check Elasticsearch Health

```bash
curl http://localhost:9200/_cluster/health
```

## Backup and Recovery

### Run Manual Backup

```bash
./deployment/scripts/backup-enhanced.sh full
```

### List Backups

```bash
./deployment/scripts/list-backups.sh
```

### Test Backup

```bash
./deployment/scripts/test-backup.sh /path/to/backup
```

### Restore from Backup

```bash
./deployment/scripts/restore-enhanced.sh /path/to/backup
```

## Monitoring

### View Metrics

```bash
curl http://localhost:8000/metrics
```

### Check Prometheus Targets

If Prometheus is configured, check targets are up.

### View Grafana Dashboards

Access Grafana at configured URL and view dashboards.

## Log Management

### View Application Logs

```bash
# Docker logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Systemd journal
journalctl -u africgraph.service -f
```

### Log Rotation

Logs are automatically rotated via logrotate:
- Location: `/etc/logrotate.d/africgraph`
- Retention: 14 days
- Compression: Enabled

## User Management

### Create User

```bash
# Via API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "secure_password",
    "role": "analyst"
  }'
```

### Reset Password

```bash
# Via API (if implemented)
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

## Performance Tuning

### Increase Neo4j Memory

Edit `docker-compose.prod.yml`:

```yaml
neo4j:
  environment:
    - NEO4J_dbms_memory_heap_max__size=4G
    - NEO4J_dbms_memory_pagecache_size=2G
```

### Increase Elasticsearch Memory

Edit `docker-compose.prod.yml`:

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
```

### Optimize Redis

```bash
# Set max memory
docker exec africgraph-redis redis-cli CONFIG SET maxmemory 1gb
docker exec africgraph-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Security Operations

### Rotate JWT Secret

1. Update `.env`:
   ```bash
   JWT_SECRET_KEY=new_secret_key
   ```

2. Restart backend:
   ```bash
   docker-compose -f docker-compose.prod.yml restart backend
   ```

3. Users will need to re-authenticate

### Update SSL Certificate

```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Review Audit Logs

```bash
# Via API
curl http://localhost:8000/api/v1/audit?limit=100

# Or query PostgreSQL directly
docker exec -it africgraph-postgres psql -U africgraph -d africgraph -c "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

## Incident Response

### Service Down

1. Check service status:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Check logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs service_name
   ```

3. Restart service:
   ```bash
   docker-compose -f docker-compose.prod.yml restart service_name
   ```

4. If still down, check resources:
   ```bash
   df -h  # Disk space
   free -h  # Memory
   docker stats  # Container resources
   ```

### Database Connection Issues

1. Check database status:
   ```bash
   ./deployment/scripts/health-check.sh
   ```

2. Check connection pool:
   ```bash
   # Neo4j
   docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "CALL dbms.listConnections()"
   ```

3. Restart database if needed:
   ```bash
   docker-compose -f docker-compose.prod.yml restart neo4j
   ```

### High Error Rate

1. Check error logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend | grep ERROR
   ```

2. Check metrics:
   ```bash
   curl http://localhost:8000/metrics | grep api_errors_total
   ```

3. Review recent changes:
   ```bash
   git log --oneline -10
   ```

4. Consider rollback if recent deployment:
   ```bash
   ./deployment/scripts/rollback.sh /path/to/backup
   ```

### Performance Degradation

1. Check system resources:
   ```bash
   docker stats
   top
   ```

2. Check slow queries:
   ```bash
   # PostgreSQL
   docker exec africgraph-postgres psql -U africgraph -d africgraph -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

3. Check cache hit rate:
   ```bash
   curl http://localhost:8000/metrics | grep cache_hit_rate
   ```

4. Clear cache if needed:
   ```bash
   curl -X POST http://localhost:8000/api/v1/cache/clear
   ```

## Maintenance Windows

### Scheduled Maintenance

1. Notify users
2. Put application in maintenance mode (if implemented)
3. Run backups
4. Perform updates
5. Run health checks
6. Remove maintenance mode

### Zero-Downtime Updates

1. Deploy to new containers
2. Health check new containers
3. Switch traffic (Nginx reload)
4. Monitor for issues
5. Remove old containers

## Emergency Procedures

### Complete System Failure

1. Check VPS status
2. Restore from backup:
   ```bash
   ./deployment/scripts/restore-enhanced.sh /path/to/latest/backup
   ```
3. Start services:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
4. Verify health:
   ```bash
   ./deployment/scripts/health-check.sh
   ```

### Data Corruption

1. Stop affected services
2. Restore from backup
3. Verify data integrity
4. Restart services
5. Monitor for issues

### Security Breach

1. Isolate affected systems
2. Preserve logs
3. Rotate all credentials
4. Review audit logs
5. Restore from clean backup
6. Patch vulnerabilities
7. Notify stakeholders

## Regular Maintenance Tasks

### Daily

- [ ] Check health status
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Check backup status

### Weekly

- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review audit logs
- [ ] Test backup restore

### Monthly

- [ ] Update dependencies
- [ ] Review and optimize queries
- [ ] Security audit
- [ ] Disaster recovery drill

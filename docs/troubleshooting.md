# Troubleshooting Guide

This guide helps resolve common issues with AfricGraph.

## Common Issues

### Services Won't Start

#### Symptoms
- Docker containers fail to start
- Services exit immediately
- Port conflicts

#### Solutions

1. **Check Docker Status**
   ```bash
   docker ps -a
   docker logs container_name
   ```

2. **Check Port Conflicts**
   ```bash
   netstat -tulpn | grep :8000
   # Or
   lsof -i :8000
   ```

3. **Check Disk Space**
   ```bash
   df -h
   docker system df
   ```

4. **Check Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs
   ```

5. **Restart Docker**
   ```bash
   sudo systemctl restart docker
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Database Connection Errors

#### Symptoms
- "Connection refused" errors
- Timeout errors
- Authentication failures

#### Solutions

1. **Check Database Status**
   ```bash
   docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
   docker exec africgraph-postgres pg_isready -U africgraph
   ```

2. **Verify Environment Variables**
   ```bash
   cat .env | grep -E "NEO4J|POSTGRES"
   ```

3. **Check Network**
   ```bash
   docker network ls
   docker network inspect africgraph-network
   ```

4. **Restart Database**
   ```bash
   docker-compose -f docker-compose.prod.yml restart neo4j postgres
   ```

### API Returns 500 Errors

#### Symptoms
- Internal server errors
- Generic error messages
- Services appear healthy

#### Solutions

1. **Check Application Logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend | tail -100
   ```

2. **Check Database Connectivity**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Memory**
   ```bash
   docker stats
   free -h
   ```

4. **Restart Backend**
   ```bash
   docker-compose -f docker-compose.prod.yml restart backend
   ```

### Slow API Responses

#### Symptoms
- High latency
- Timeout errors
- Slow page loads

#### Solutions

1. **Check Database Performance**
   ```bash
   # PostgreSQL slow queries
   docker exec africgraph-postgres psql -U africgraph -d africgraph -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

2. **Check Cache Hit Rate**
   ```bash
   curl http://localhost:8000/metrics | grep cache_hit_rate
   ```

3. **Clear and Warm Cache**
   ```bash
   curl -X POST http://localhost:8000/api/v1/cache/clear
   curl -X POST http://localhost:8000/api/v1/cache/warm
   ```

4. **Check System Resources**
   ```bash
   top
   docker stats
   ```

5. **Optimize Queries**
   - Review slow query logs
   - Add database indexes
   - Optimize Cypher queries

### Authentication Issues

#### Symptoms
- "Invalid token" errors
- Login failures
- Permission denied errors

#### Solutions

1. **Check JWT Configuration**
   ```bash
   cat .env | grep JWT
   ```

2. **Verify Token Expiration**
   - Check token expiration time
   - Re-authenticate if expired

3. **Check User Permissions**
   ```bash
   # Via API
   curl http://localhost:8000/api/v1/users/me
   ```

4. **Reset User Password** (if implemented)
   ```bash
   curl -X POST http://localhost:8000/api/auth/reset-password
   ```

### Graph Queries Fail

#### Symptoms
- Graph queries return empty results
- Timeout errors
- Incorrect results

#### Solutions

1. **Check Neo4j Status**
   ```bash
   docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n) RETURN count(n)"
   ```

2. **Verify Data Exists**
   ```bash
   # In Neo4j Browser
   MATCH (n) RETURN n LIMIT 10
   ```

3. **Check Query Syntax**
   - Review Cypher query syntax
   - Test in Neo4j Browser

4. **Check Permissions**
   - Verify ABAC filters aren't too restrictive
   - Check user permissions

### Search Not Working

#### Symptoms
- Search returns no results
- Search is slow
- Autocomplete not working

#### Solutions

1. **Check Elasticsearch Status**
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

2. **Reindex Data**
   ```bash
   curl -X POST http://localhost:8000/api/v1/search/index/all
   ```

3. **Check Index Status**
   ```bash
   curl http://localhost:9200/_cat/indices
   ```

4. **Verify Data Indexed**
   ```bash
   curl http://localhost:9200/businesses/_search?q=*
   ```

### Backup Failures

#### Symptoms
- Backup script fails
- Backup files missing
- Backup size is zero

#### Solutions

1. **Check Disk Space**
   ```bash
   df -h /var/backups
   ```

2. **Check Permissions**
   ```bash
   ls -la /var/backups/africgraph
   ```

3. **Test Backup Manually**
   ```bash
   ./deployment/scripts/backup-enhanced.sh full
   ```

4. **Check Database Connectivity**
   ```bash
   ./deployment/scripts/health-check.sh
   ```

5. **Review Backup Logs**
   ```bash
   journalctl -u africgraph-backup.service
   ```

### SSL Certificate Issues

#### Symptoms
- SSL errors in browser
- Certificate expired
- Mixed content warnings

#### Solutions

1. **Check Certificate Status**
   ```bash
   sudo certbot certificates
   ```

2. **Renew Certificate**
   ```bash
   sudo certbot renew
   sudo systemctl reload nginx
   ```

3. **Check Nginx Configuration**
   ```bash
   sudo nginx -t
   ```

4. **Verify Certificate Files**
   ```bash
   sudo ls -la /etc/letsencrypt/live/yourdomain.com/
   ```

### Frontend Not Loading

#### Symptoms
- Blank page
- JavaScript errors
- API connection errors

#### Solutions

1. **Check Browser Console**
   - Open browser DevTools
   - Check for JavaScript errors
   - Check Network tab

2. **Verify API URL**
   - Check `REACT_APP_API_URL` in frontend `.env`
   - Verify API is accessible

3. **Check Frontend Build**
   ```bash
   cd frontend
   npm run build
   ```

4. **Check Nginx Configuration**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

### Memory Issues

#### Symptoms
- Out of memory errors
- Services killed by OOM killer
- Slow performance

#### Solutions

1. **Check Memory Usage**
   ```bash
   free -h
   docker stats
   ```

2. **Increase Container Memory**
   - Edit `docker-compose.prod.yml`
   - Add memory limits
   - Restart containers

3. **Optimize Application**
   - Review memory-intensive operations
   - Implement pagination
   - Clear caches

4. **Upgrade VPS**
   - Increase RAM allocation
   - Consider dedicated server

### Disk Space Issues

#### Symptoms
- "No space left on device" errors
- Services fail to start
- Backup failures

#### Solutions

1. **Check Disk Usage**
   ```bash
   df -h
   du -sh /var/lib/docker
   ```

2. **Clean Docker**
   ```bash
   docker system prune -a
   docker volume prune
   ```

3. **Clean Logs**
   ```bash
   journalctl --vacuum-time=7d
   ```

4. **Clean Old Backups**
   ```bash
   find /var/backups/africgraph -type f -mtime +30 -delete
   ```

5. **Increase Disk Space**
   - Expand VPS disk
   - Move data to external storage

## Debugging Tips

### Enable Debug Logging

```bash
# Backend
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.prod.yml restart backend

# Or in .env
LOG_LEVEL=DEBUG
```

### Use Docker Exec

```bash
# Access container shell
docker exec -it africgraph-backend bash

# Run commands
docker exec africgraph-backend python -c "from src.api.main import app; print(app)"
```

### Check Network

```bash
# Test connectivity
docker exec africgraph-backend ping neo4j
docker exec africgraph-backend ping postgres
```

### Review Configuration

```bash
# Check environment variables
docker exec africgraph-backend env | grep -E "NEO4J|POSTGRES|REDIS"
```

## Getting Help

If issues persist:

1. **Collect Information**
   - Error messages
   - Logs
   - System status
   - Recent changes

2. **Check Documentation**
   - [Architecture Overview](./architecture.md)
   - [Deployment Guide](./deployment.md)
   - [Runbooks](./runbooks.md)

3. **Review Logs**
   ```bash
   ./deployment/scripts/logs.sh
   journalctl -u africgraph.service
   ```

4. **Contact Support**
   - Open GitHub issue
   - Contact system administrator
   - Check status page

## Prevention

### Regular Maintenance

- Monitor health checks daily
- Review logs weekly
- Update dependencies monthly
- Test backups regularly

### Monitoring

- Set up alerts for:
  - High error rates
  - Slow queries
  - Disk space
  - Memory usage
  - Service downtime

### Documentation

- Document custom configurations
- Keep runbooks updated
- Document known issues and solutions

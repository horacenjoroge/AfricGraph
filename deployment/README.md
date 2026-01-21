# AfricGraph VPS Deployment Guide

This guide covers deploying AfricGraph on a VPS using Docker Compose, Nginx, and Let's Encrypt SSL.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Root or sudo access
- Domain name pointing to your VPS IP
- At least 4GB RAM, 2 CPU cores, 50GB disk space

## Quick Start

### 1. Initial VPS Setup

```bash
# Run the setup script
./deployment/scripts/setup-vps.sh
```

This will install:
- Docker and Docker Compose
- Nginx
- Certbot (for SSL)
- Git, curl, wget
- UFW firewall
- Fail2ban

### 2. Clone Repository

```bash
cd /opt/africgraph
git clone https://github.com/yourusername/AfricGraph.git .
```

### 3. Configure Environment

```bash
# Copy environment template
cp deployment/env.template .env

# Edit .env with your configuration
nano .env
```

**Important variables to set:**
- `NEO4J_PASSWORD`: Strong password for Neo4j
- `POSTGRES_PASSWORD`: Strong password for PostgreSQL
- `RABBITMQ_PASSWORD`: Strong password for RabbitMQ
- `JWT_SECRET_KEY`: Strong random secret for JWT tokens
- `CORS_ORIGINS`: Your domain(s), e.g., `https://yourdomain.com`
- `REACT_APP_API_URL`: Your API URL, e.g., `https://yourdomain.com/api`

### 4. Setup SSL Certificate

```bash
./deployment/scripts/setup-ssl.sh yourdomain.com your@email.com
```

This will:
- Obtain SSL certificate from Let's Encrypt
- Configure auto-renewal
- Update Nginx configuration

### 5. Configure Nginx

```bash
# Copy Nginx configuration
sudo cp deployment/nginx/africgraph.conf /etc/nginx/sites-available/africgraph.conf

# Update domain in config
sudo sed -i "s/yourdomain.com/your-actual-domain.com/g" /etc/nginx/sites-available/africgraph.conf

# Enable site
sudo ln -s /etc/nginx/sites-available/africgraph.conf /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 6. Deploy Application

```bash
./deployment/scripts/deploy.sh production
```

This will:
- Pull latest code
- Build Docker images
- Start all services
- Run database migrations
- Warm up cache

### 7. Setup Systemd Services

```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo cp deployment/systemd/*.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable africgraph.service
sudo systemctl start africgraph.service

# Enable backup timer (runs daily at 3 AM)
sudo systemctl enable africgraph-backup.timer
sudo systemctl start africgraph-backup.timer
```

## Manual Operations

### Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services

```bash
docker-compose -f docker-compose.prod.yml restart
```

### Health Check

```bash
./deployment/scripts/health-check.sh
```

## Backup and Restore

### Manual Backup

```bash
./deployment/scripts/backup.sh
```

Backups are stored in `/var/backups/africgraph/` and include:
- PostgreSQL database dump
- Neo4j database dump
- Redis data (if enabled)
- Elasticsearch snapshots

### Restore from Backup

```bash
./deployment/scripts/restore-backup.sh /var/backups/africgraph/africgraph_backup_YYYYMMDD_HHMMSS.tar.gz
```

**Warning:** This will overwrite existing data!

## CI/CD Deployment

### GitHub Actions Setup

1. Add secrets to your GitHub repository:
   - `VPS_HOST`: Your VPS IP or domain
   - `VPS_USER`: SSH user (usually `root` or `ubuntu`)
   - `VPS_SSH_KEY`: Private SSH key for deployment

2. Push to `main` or `master` branch to trigger deployment

3. Or manually trigger via GitHub Actions UI

### SSH Key Setup

```bash
# On your local machine
ssh-keygen -t ed25519 -C "deploy@africgraph" -f ~/.ssh/africgraph_deploy

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/africgraph_deploy.pub user@your-vps

# Add private key to GitHub secrets
cat ~/.ssh/africgraph_deploy
# Copy output and paste into GitHub secret VPS_SSH_KEY
```

## Monitoring

### View Metrics

Prometheus metrics are available at:
- Internal: `http://localhost:8000/metrics`
- External: `https://yourdomain.com/metrics` (restricted by IP)

### Grafana Setup

1. Install Grafana on VPS or separate server
2. Configure Prometheus as data source
3. Import dashboards from `backend/monitoring/grafana/dashboards/`

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check system resources
df -h
free -h
```

### Database Connection Issues

```bash
# Test PostgreSQL
docker exec africgraph-postgres pg_isready -U africgraph

# Test Neo4j
docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/africgraph_error.log
```

## Security Best Practices

1. **Firewall**: UFW is configured to allow only SSH, HTTP, and HTTPS
2. **Fail2ban**: Protects against brute force attacks
3. **SSL**: Let's Encrypt certificates with auto-renewal
4. **Secrets**: Store sensitive data in `.env` file (never commit to git)
5. **Updates**: Regularly update system packages and Docker images
6. **Backups**: Automated daily backups with retention policy

## Maintenance

### Update Application

```bash
cd /opt/africgraph
git pull
./deployment/scripts/deploy.sh production
```

### Update Docker Images

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune
```

## Scaling

For higher traffic, consider:

1. **Horizontal Scaling**: Run multiple backend instances behind load balancer
2. **Database**: Use managed PostgreSQL/Neo4j services
3. **Cache**: Use Redis cluster for distributed caching
4. **CDN**: Use CloudFlare or similar for static assets

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Run health check: `./deployment/scripts/health-check.sh`
- Review documentation in `docs/` directory

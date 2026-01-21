# Deployment Guide

This guide covers deploying AfricGraph to a VPS using Docker Compose, Nginx, and Let's Encrypt SSL.

## Quick Start

For a quick deployment, see [deployment/QUICK_START.md](../deployment/QUICK_START.md).

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Root or sudo access
- Domain name pointing to your VPS IP
- At least 4GB RAM, 2 CPU cores, 50GB disk space

## Initial Setup

### 1. Run Setup Script

```bash
./deployment/scripts/setup-vps.sh
```

This installs:
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
cp deployment/env.template .env
nano .env
```

**Required Configuration:**
- Database passwords (Neo4j, PostgreSQL, RabbitMQ)
- JWT secret key
- CORS origins (your domain)
- API URL for frontend

## SSL Setup

### Obtain SSL Certificate

```bash
./deployment/scripts/setup-ssl.sh yourdomain.com your@email.com
```

This will:
- Obtain SSL certificate from Let's Encrypt
- Configure auto-renewal
- Update Nginx configuration

## Nginx Configuration

### 1. Copy Configuration

```bash
sudo cp deployment/nginx/africgraph.conf /etc/nginx/sites-available/africgraph.conf
```

### 2. Update Domain

```bash
sudo sed -i "s/yourdomain.com/your-actual-domain.com/g" /etc/nginx/sites-available/africgraph.conf
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/africgraph.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optional
```

### 4. Test and Reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Deploy Application

### Initial Deployment

```bash
./deployment/scripts/deploy.sh production
```

This will:
- Pull latest code
- Build Docker images
- Start all services
- Run database migrations
- Warm up cache

### Update Application

```bash
./deployment/scripts/update.sh production
```

## Systemd Services

### Setup Services

```bash
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo cp deployment/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

### Enable Services

```bash
sudo systemctl enable africgraph.service
sudo systemctl start africgraph.service

sudo systemctl enable africgraph-backup.timer
sudo systemctl start africgraph-backup.timer
```

## Health Checks

### Manual Health Check

```bash
./deployment/scripts/health-check.sh
```

### Automated Monitoring

Health checks are available at:
- `/health` - Application health
- `/metrics` - Prometheus metrics (restricted)

## Backup Configuration

### Automated Backups

Backups run daily at 3 AM via systemd timer. Configure backup settings in `.env`:

```bash
BACKUP_DIR=/var/backups/africgraph
BACKUP_CLOUD_PROVIDER=s3  # Optional: s3, gcs, azure
S3_BACKUP_BUCKET=africgraph-backups
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Manual Backup

```bash
./deployment/scripts/backup-enhanced.sh full
```

## Scaling

### Horizontal Scaling

For higher traffic:

1. **Multiple Backend Instances**
   - Run multiple backend containers
   - Use Nginx load balancing
   - Configure sticky sessions if needed

2. **Database Scaling**
   - Use managed PostgreSQL/Neo4j services
   - Configure read replicas
   - Optimize queries

3. **Cache Scaling**
   - Use Redis cluster
   - Increase cache TTL for stable data

## Monitoring

### Prometheus Metrics

Metrics are available at `/metrics` (IP-restricted). Configure Prometheus to scrape:

```yaml
scrape_configs:
  - job_name: 'africgraph'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Import dashboards from `backend/monitoring/grafana/dashboards/`:
- System Health
- Business Metrics
- Performance Metrics
- User Activity

## Troubleshooting

See [Troubleshooting Guide](./troubleshooting.md) for common issues.

## CI/CD Deployment

### GitHub Actions

Configure secrets in GitHub:
- `VPS_HOST`: Your VPS IP or domain
- `VPS_USER`: SSH user
- `VPS_SSH_KEY`: Private SSH key

Deployment runs automatically on push to main/master.

### Manual Deployment

```bash
cd /opt/africgraph
git pull
./deployment/scripts/deploy.sh production
```

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] Fail2ban enabled
- [ ] SSL certificate installed
- [ ] Strong passwords set
- [ ] Secrets in `.env` (not committed)
- [ ] Regular backups configured
- [ ] Monitoring enabled
- [ ] Log rotation configured

## Maintenance

### Regular Tasks

- **Daily**: Monitor health checks
- **Weekly**: Review logs, check disk space
- **Monthly**: Update dependencies, test backups
- **Quarterly**: Security audit, disaster recovery drill

### Update Dependencies

```bash
# Update application
./deployment/scripts/update.sh production

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Disaster Recovery

See [Disaster Recovery Plan](../deployment/DISASTER_RECOVERY_PLAN.md) for recovery procedures.

## Support

For deployment issues:
1. Check [Troubleshooting Guide](./troubleshooting.md)
2. Review logs: `./deployment/scripts/logs.sh`
3. Run health check: `./deployment/scripts/health-check.sh`

# Quick Start Guide

## First-Time Deployment

```bash
# 1. Setup VPS
./deployment/scripts/setup-vps.sh

# 2. Clone repository
cd /opt/africgraph
git clone <your-repo-url> .

# 3. Configure environment
cp deployment/env.template .env
nano .env  # Edit with your values

# 4. Setup SSL
./deployment/scripts/setup-ssl.sh yourdomain.com your@email.com

# 5. Configure Nginx
sudo cp deployment/nginx/africgraph.conf /etc/nginx/sites-available/africgraph.conf
sudo sed -i "s/yourdomain.com/your-actual-domain.com/g" /etc/nginx/sites-available/africgraph.conf
sudo ln -s /etc/nginx/sites-available/africgraph.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 6. Deploy
./deployment/scripts/deploy.sh production

# 7. Setup systemd services
sudo cp deployment/systemd/*.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now africgraph.service africgraph-backup.timer
```

## Daily Operations

```bash
# View logs
./deployment/scripts/logs.sh

# Health check
./deployment/scripts/health-check.sh

# Update application
./deployment/scripts/update.sh production

# Manual backup
./deployment/scripts/backup.sh
```

## Common Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# View service status
docker-compose -f docker-compose.prod.yml ps

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend bash
```

## Troubleshooting

```bash
# Check logs
./deployment/scripts/logs.sh backend

# Health check
./deployment/scripts/health-check.sh

# Restart all services
docker-compose -f docker-compose.prod.yml restart
```

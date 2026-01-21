#!/bin/bash
# VPS setup script for AfricGraph

set -e

echo "Setting up VPS for AfricGraph deployment..."

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    ufw \
    fail2ban

# Start and enable Docker
echo "Configuring Docker..."
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group
sudo usermod -aG docker $USER

# Configure firewall
echo "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configure fail2ban
echo "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/africgraph
sudo chown $USER:$USER /opt/africgraph

# Create backup directory
echo "Creating backup directory..."
sudo mkdir -p /var/backups/africgraph
sudo chown $USER:$USER /var/backups/africgraph

# Setup log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/africgraph > /dev/null <<EOF
/opt/africgraph/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $USER $USER
}
EOF

echo "VPS setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository to /opt/africgraph"
echo "2. Copy deployment/env.template to .env and configure it"
echo "3. Run: ./deployment/scripts/setup-ssl.sh yourdomain.com your@email.com"
echo "4. Run: ./deployment/scripts/deploy.sh production"
echo "5. Setup systemd services: sudo cp deployment/systemd/*.service /etc/systemd/system/"
echo "6. Enable services: sudo systemctl enable africgraph.service africgraph-backup.timer"

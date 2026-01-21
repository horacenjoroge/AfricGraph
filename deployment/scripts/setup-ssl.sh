#!/bin/bash
# SSL/TLS setup script using Let's Encrypt

set -e

DOMAIN="${1:-yourdomain.com}"
EMAIL="${2:-admin@${DOMAIN}}"

echo "Setting up SSL certificate for ${DOMAIN}"

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Create directory for ACME challenge
sudo mkdir -p /var/www/certbot

# Obtain certificate
echo "Obtaining SSL certificate..."
sudo certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    --domains "${DOMAIN},www.${DOMAIN}"

# Update nginx config with domain
sudo sed -i "s/yourdomain.com/${DOMAIN}/g" /etc/nginx/sites-available/africgraph.conf

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Setup auto-renewal
echo "Setting up auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo "SSL certificate setup complete!"
echo "Certificate will auto-renew via certbot timer."

#!/bin/bash
# Usage: bash deploy/nginx_setup.sh yourdomain.com
# Installs nginx config and obtains a free SSL certificate via Let's Encrypt.

set -e
DOMAIN=${1:?'Usage: bash nginx_setup.sh yourdomain.com'}

# Copy and configure nginx
sed "s/YOURDOMAIN/$DOMAIN/g" /opt/geographybot/deploy/nginx.conf \
    > /etc/nginx/sites-available/geographybot

ln -sf /etc/nginx/sites-available/geographybot /etc/nginx/sites-enabled/geographybot
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

# Obtain SSL certificate
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN"

systemctl reload nginx

echo ""
echo "✅ Nginx configured for https://$DOMAIN"
echo "   Mini App: https://$DOMAIN/app/index.html"
echo "   API:      https://$DOMAIN/api/"
echo ""
echo "Set in .env:"
echo "   WEBAPP_URL=https://$DOMAIN/app/index.html"
echo "Then restart the bot: systemctl restart geographybot"

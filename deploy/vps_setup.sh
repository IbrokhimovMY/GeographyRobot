#!/bin/bash
# Run once on a fresh Ubuntu 22.04 / Debian 12 VPS as root.
# Usage:  bash deploy/vps_setup.sh

set -e

# ── 1. System packages ────────────────────────────────────────
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# ── 2. Bot user & directory ───────────────────────────────────
useradd -r -s /bin/false -m -d /opt/geographybot geographybot 2>/dev/null || true
mkdir -p /opt/geographybot
chown geographybot:geographybot /opt/geographybot

echo ""
echo "✅ System packages installed."
echo ""
echo "Next steps:"
echo "  1. Copy your project to /opt/geographybot/"
echo "     git clone https://github.com/YOUR/REPO /opt/geographybot"
echo "  2. Create /opt/geographybot/.env  (copy from .env.example)"
echo "  3. Run:  bash deploy/vps_install.sh"
echo "  4. Run:  bash deploy/nginx_setup.sh yourdomain.com"

#!/bin/bash
# Run from /opt/geographybot after cloning the repo.
# Sets up the virtualenv, generates webapp data, and installs the systemd service.

set -e
cd /opt/geographybot

# ── virtualenv ────────────────────────────────────────────────
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

# ── generate Mini App data ────────────────────────────────────
.venv/bin/python generate_webapp_data.py

# ── systemd service ───────────────────────────────────────────
cp deploy/geographybot.service /etc/systemd/system/geographybot.service
systemctl daemon-reload
systemctl enable geographybot
systemctl restart geographybot

echo ""
echo "✅ Bot installed and running."
echo "   Status:  systemctl status geographybot"
echo "   Logs:    journalctl -u geographybot -f"

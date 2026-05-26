#!/bin/bash
# Run from /opt/geographybot to pull latest code and restart the bot.

set -e
cd /opt/geographybot

git pull
.venv/bin/pip install -r requirements.txt -q
.venv/bin/python generate_webapp_data.py

systemctl restart geographybot
echo "✅ Updated and restarted."
journalctl -u geographybot -n 20 --no-pager

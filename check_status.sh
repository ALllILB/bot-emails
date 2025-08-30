#!/bin/bash

echo "=== Email Bot Status Check ==="
echo

echo "1. Service Status:"
sudo systemctl status log-viewer.service --no-pager -l
echo
sudo systemctl status email-processor.service --no-pager -l
echo
sudo systemctl status whatsapp-bot.service --no-pager -l
echo

echo "2. Log Files:"
ls -la /opt/email-bot/*.log 2>/dev/null || echo "No log files found"
echo

echo "3. Configuration:"
if [ -f /opt/email-bot/.env ]; then
    echo ".env file exists"
    echo "Environment variables configured:"
    grep -v "PASS\|TOKEN\|KEY" /opt/email-bot/.env | head -5
else
    echo "ERROR: .env file not found!"
fi
echo

echo "4. Network:"
netstat -tlnp | grep :8223 || echo "Port 8223 not listening"
echo

echo "5. Recent Errors:"
journalctl -u log-viewer.service --no-pager -n 5 2>/dev/null
echo
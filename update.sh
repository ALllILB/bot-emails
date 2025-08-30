#!/bin/bash

# Email Bot GitHub Updater
# Usage: ./update.sh [repository-url]

set -e

INSTALL_DIR="/opt/email-bot"
SERVICE_USER="emailbot"
REPO_URL="${1:-https://github.com/your-username/bot-emails.git}"
TEMP_DIR="/tmp/bot-emails-update"

echo "Updating Email Bot from GitHub..."

# Stop services
echo "Stopping services..."
sudo systemctl stop email-processor.service whatsapp-bot.service log-viewer.service 2>/dev/null || true

# Backup .env file
echo "Backing up configuration..."
sudo cp $INSTALL_DIR/.env /tmp/.env.backup 2>/dev/null || true

# Clone latest version
echo "Downloading latest version..."
rm -rf $TEMP_DIR
git clone $REPO_URL $TEMP_DIR

# Update files
echo "Updating files..."
sudo cp -r $TEMP_DIR/* $INSTALL_DIR/
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Restore .env file
sudo cp /tmp/.env.backup $INSTALL_DIR/.env 2>/dev/null || true
sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env 2>/dev/null || true

# Update dependencies
echo "Updating dependencies..."
cd $INSTALL_DIR
sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt --upgrade

# Reload systemd and update services
sudo systemctl daemon-reload
sudo systemctl enable email-processor.service whatsapp-bot.service log-viewer.service

# Start services
echo "Starting services..."
sudo systemctl start log-viewer.service
sudo systemctl start email-processor.service whatsapp-bot.service

# Cleanup
rm -rf $TEMP_DIR

echo "Update completed!"
echo "Check status: sudo systemctl status log-viewer email-processor whatsapp-bot"
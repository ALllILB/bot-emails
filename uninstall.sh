#!/bin/bash

# Email Bot Uninstaller for Ubuntu Server

set -e

# Variables
SERVICE_NAME="email-bot"
INSTALL_DIR="/opt/email-bot"
SERVICE_USER="emailbot"

echo "Uninstalling Email Bot Service..."

# Stop and disable services
sudo systemctl stop email-processor.service whatsapp-bot.service log-viewer.service 2>/dev/null || true
sudo systemctl disable email-processor.service whatsapp-bot.service log-viewer.service 2>/dev/null || true

# Remove systemd service files
sudo rm -f /etc/systemd/system/email-processor.service
sudo rm -f /etc/systemd/system/whatsapp-bot.service
sudo rm -f /etc/systemd/system/log-viewer.service

# Reload systemd
sudo systemctl daemon-reload

# Remove installation directory
sudo rm -rf $INSTALL_DIR

# Remove service user
sudo userdel $SERVICE_USER 2>/dev/null || true

echo "Uninstallation completed!"
echo "Email Bot services have been removed from the system."
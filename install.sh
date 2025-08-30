#!/bin/bash

# Email Bot Installer for Ubuntu Server

set -e

# Variables
SERVICE_NAME="email-bot"
INSTALL_DIR="/opt/email-bot"
SERVICE_USER="emailbot"
CURRENT_DIR=$(pwd)

echo "Installing Email Bot Service..."

# Create service user
sudo useradd -r -s /bin/false $SERVICE_USER 2>/dev/null || true

# Create installation directory
sudo mkdir -p $INSTALL_DIR
sudo cp -r * $INSTALL_DIR/
sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Copy .env.example to .env if not exists
if [ ! -f $INSTALL_DIR/.env ]; then
    sudo cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env
    sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env
fi

# Install Python dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
cd $INSTALL_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

# Create systemd service files
sudo tee /etc/systemd/system/email-processor.service > /dev/null <<EOF
[Unit]
Description=Email Processor Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python email_processor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/whatsapp-bot.service > /dev/null <<EOF
[Unit]
Description=WhatsApp Bot Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/log-viewer.service > /dev/null <<EOF
[Unit]
Description=Bot Log Viewer Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python log_viewer.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable email-processor.service
sudo systemctl enable whatsapp-bot.service
sudo systemctl enable log-viewer.service

echo "Installation completed!"
echo "IMPORTANT: Configure your credentials in: $INSTALL_DIR/.env"
echo "Then start services with: sudo systemctl start log-viewer"
echo "Check status with: sudo systemctl status log-viewer"
echo "View logs at: http://$(hostname -I | awk '{print $1}'):8223"
echo "After configuring .env, start other services: sudo systemctl start email-processor whatsapp-bot"
#!/bin/bash

#############################################
# Free Game Checker - LXC Install Script
# For Proxmox LXC Container (Debian/Ubuntu)
#############################################

set -e

echo "========================================="
echo "  Free Game Checker Installation Script"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1:${NC} Updating system packages..."
apt-get update
apt-get upgrade -y

echo ""
echo -e "${GREEN}Step 2:${NC} Installing required packages..."
apt-get install -y python3 python3-pip python3-venv git curl

echo ""
echo -e "${GREEN}Step 3:${NC} Creating application user..."
if ! id "gamecheck" &>/dev/null; then
    useradd -r -s /bin/bash -d /opt/free-game-checker gamecheck
    echo "User 'gamecheck' created"
else
    echo "User 'gamecheck' already exists"
fi

echo ""
echo -e "${GREEN}Step 4:${NC} Cloning repository from GitHub..."
if [ -d "/opt/free-game-checker" ]; then
    echo "Directory exists, updating..."
    cd /opt/free-game-checker
    git pull
else
    git clone https://github.com/MatDaBoss/free-game-checker.git /opt/free-game-checker
fi

cd /opt/free-game-checker

echo ""
echo -e "${GREEN}Step 5:${NC} Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo -e "${GREEN}Step 6:${NC} Creating configuration directories..."
mkdir -p /etc/free-game-checker
mkdir -p /var/lib/free-game-checker
mkdir -p /var/log

echo ""
echo -e "${GREEN}Step 7:${NC} Creating default configuration..."
cat > /etc/free-game-checker/config.json << 'EOF'
{
    "email_sender": "freegamechecker@gmail.com",
    "email_password": "",
    "schedule_day": "friday",
    "schedule_time": "09:00",
    "enabled_stores": [
        "Epic Games Store",
        "Steam",
        "GOG",
        "Humble Bundle",
        "Itch.io",
        "Prime Gaming",
        "Google Play Games"
    ]
}
EOF

echo ""
echo -e "${GREEN}Step 8:${NC} Setting permissions..."
chown -R gamecheck:gamecheck /opt/free-game-checker
chown -R gamecheck:gamecheck /var/lib/free-game-checker
chown -R gamecheck:gamecheck /etc/free-game-checker
touch /var/log/free-game-checker.log
chown gamecheck:gamecheck /var/log/free-game-checker.log

echo ""
echo -e "${GREEN}Step 9:${NC} Creating systemd service for game checker..."
cat > /etc/systemd/system/free-game-checker.service << 'EOF'
[Unit]
Description=Free Game Checker Service
After=network.target

[Service]
Type=simple
User=gamecheck
WorkingDirectory=/opt/free-game-checker
ExecStart=/opt/free-game-checker/venv/bin/python3 /opt/free-game-checker/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo -e "${GREEN}Step 10:${NC} Creating systemd service for web interface..."
cat > /etc/systemd/system/free-game-checker-web.service << 'EOF'
[Unit]
Description=Free Game Checker Web Interface
After=network.target

[Service]
Type=simple
User=gamecheck
WorkingDirectory=/opt/free-game-checker
ExecStart=/opt/free-game-checker/venv/bin/python3 /opt/free-game-checker/web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo -e "${GREEN}Step 11:${NC} Reloading systemd and enabling services..."
systemctl daemon-reload
systemctl enable free-game-checker
systemctl enable free-game-checker-web

echo ""
echo -e "${GREEN}Step 12:${NC} Starting services..."
systemctl start free-game-checker-web

echo ""
echo "========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "========================================="
echo ""
echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo ""
echo "1. Find your container's IP address:"
echo -e "   ${GREEN}ip addr show${NC}"
echo ""
echo "2. Access the web interface from your browser:"
echo -e "   ${GREEN}http://YOUR_CONTAINER_IP:5000${NC}"
echo ""
echo "3. Go to Settings and enter your Gmail app password:"
echo "   (Get it from: https://myaccount.google.com/apppasswords)"
echo ""
echo "4. Add email recipients who should receive notifications"
echo ""
echo "5. Customize your schedule and store preferences"
echo ""
echo "6. Click 'Check for Games Now' to test it!"
echo ""
echo "7. Start the game checker service when ready:"
echo -e "   ${GREEN}systemctl start free-game-checker${NC}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View web interface status: systemctl status free-game-checker-web"
echo "  View checker status: systemctl status free-game-checker"
echo "  View logs: tail -f /var/log/free-game-checker.log"
echo "  Restart services: systemctl restart free-game-checker"
echo ""
echo "========================================="

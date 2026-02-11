#!/bin/bash

###############################################################################
# Free Game Checker - Complete Proxmox LXC Setup Script
# 
# This script creates and configures an LXC container on Proxmox,
# then installs the Free Game Checker application automatically.
#
# Run this ON YOUR PROXMOX HOST (not in a container)
#
# USAGE:
#   rm -f proxmox-lxc-setup.sh*
#   wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh
#   chmod +x proxmox-lxc-setup.sh
#   ./proxmox-lxc-setup.sh
#
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
CONTAINER_NAME="free-game-checker"
CONTAINER_HOSTNAME="free-game-checker"
CONTAINER_PASSWORD="FreeGames2026!"
GITHUB_REPO="https://github.com/MatDaBoss/free-game-checker.git"

# Container specifications
DISK_SIZE="8"
RAM="512"
SWAP="512"
CPU_CORES="1"
STORAGE="local-lvm"
TEMPLATE_STORAGE="local"
BRIDGE="vmbr0"

# Template settings
TEMPLATE_NAME="ubuntu-22.04-standard"
OSTYPE="ubuntu"

###############################################################################
# Functions
###############################################################################

get_next_ctid() {
    local next_id=100
    while true; do
        if pct status $next_id &>/dev/null; then
            ((next_id++))
            continue
        fi
        if qm status $next_id &>/dev/null; then
            ((next_id++))
            continue
        fi
        break
    done
    echo $next_id
}

print_header() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✔ $1${NC}"
}

print_error() {
    echo -e "${RED}✖ $1${NC}"
}

check_proxmox() {
    if ! command -v pct &> /dev/null; then
        print_error "This script must be run on a Proxmox host!"
        exit 1
    fi
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

download_template() {
    print_step "Checking for Ubuntu 22.04 template..."
    
    if pveam list $TEMPLATE_STORAGE | grep -q "ubuntu-22.04"; then
        print_success "Ubuntu 22.04 template already downloaded"
        TEMPLATE=$(pveam list $TEMPLATE_STORAGE | grep ubuntu-22.04 | head -n 1 | awk '{print $1}')
    else
        print_step "Downloading Ubuntu 22.04 template..."
        TEMPLATE=$(pveam available | grep ubuntu-22.04 | head -n 1 | awk '{print $2}')
        pveam download $TEMPLATE_STORAGE $TEMPLATE
        print_success "Template downloaded"
    fi
}

create_container() {
    print_step "Creating LXC container (ID: $CTID)..."
    
    pct create $CTID $TEMPLATE_STORAGE:vztmpl/$(basename $TEMPLATE) \
        --hostname $CONTAINER_HOSTNAME \
        --password "$CONTAINER_PASSWORD" \
        --cores $CPU_CORES \
        --memory $RAM \
        --swap $SWAP \
        --rootfs $STORAGE:$DISK_SIZE \
        --net0 name=eth0,bridge=$BRIDGE,ip=dhcp \
        --ostype $OSTYPE \
        --unprivileged 1 \
        --features nesting=1 \
        --onboot 1 \
        --start 0
    
    print_success "Container created successfully (CTID: $CTID)"
}

start_container() {
    print_step "Starting container..."
    pct start $CTID
    
    print_info "Waiting for container to boot..."
    sleep 10
    
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if pct exec $CTID -- ip addr show eth0 | grep -q "inet "; then
            print_success "Container is online"
            break
        fi
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Container failed to get network connection"
        exit 1
    fi
}

install_application() {
    print_step "Installing Free Game Checker..."
    
    print_info "Updating system packages..."
    pct exec $CTID -- bash -c "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y"
    
    print_info "Installing dependencies..."
    pct exec $CTID -- bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv git curl wget"
    
    print_info "Creating application user..."
    pct exec $CTID -- bash -c "useradd -r -s /bin/bash -d /opt/free-game-checker gamecheck || true"
    
    print_info "Downloading Free Game Checker from GitHub..."
    pct exec $CTID -- bash -c "git clone $GITHUB_REPO /opt/free-game-checker"
    
    print_info "Setting up Python environment..."
    pct exec $CTID -- bash -c "cd /opt/free-game-checker && python3 -m venv venv"
    pct exec $CTID -- bash -c "cd /opt/free-game-checker && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    print_info "Creating configuration directories..."
    pct exec $CTID -- bash -c "mkdir -p /etc/free-game-checker /var/lib/free-game-checker /var/log"
    
    print_info "Creating default configuration..."
    pct exec $CTID -- bash -c 'cat > /etc/free-game-checker/config.json << "EOF"
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
        "Nintendo Switch",
        "Xbox Store",
        "Google Play Games"
    ]
}
EOF'
    
    print_info "Setting permissions..."
    pct exec $CTID -- bash -c "chown -R gamecheck:gamecheck /opt/free-game-checker /var/lib/free-game-checker /etc/free-game-checker"
    pct exec $CTID -- bash -c "touch /var/log/free-game-checker.log && chown gamecheck:gamecheck /var/log/free-game-checker.log"
    
    print_info "Creating systemd services..."
    
    pct exec $CTID -- bash -c 'cat > /etc/systemd/system/free-game-checker.service << "EOF"
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
EOF'
    
    pct exec $CTID -- bash -c 'cat > /etc/systemd/system/free-game-checker-web.service << "EOF"
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
EOF'
    
    print_info "Enabling and starting services..."
    pct exec $CTID -- bash -c "systemctl daemon-reload"
    pct exec $CTID -- bash -c "systemctl enable free-game-checker free-game-checker-web"
    pct exec $CTID -- bash -c "systemctl start free-game-checker-web"
    
    print_success "Free Game Checker installed and running!"
}

get_container_ip() {
    print_step "Getting container IP address..."
    
    local max_attempts=10
    local attempt=0
    local container_ip=""
    
    while [ $attempt -lt $max_attempts ]; do
        container_ip=$(pct exec $CTID -- ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d'/' -f1)
        if [ ! -z "$container_ip" ]; then
            break
        fi
        sleep 2
        ((attempt++))
    done
    
    echo "$container_ip"
}

print_final_info() {
    local container_ip=$1
    
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${GREEN}     🎉 Installation Complete!${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
    echo -e "${GREEN}🌐 Access Free Game Checker:${NC}"
    echo -e "   ${BLUE}http://${container_ip}:5000${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📋 Container Details:${NC}"
    echo -e "   Container ID:    ${GREEN}$CTID${NC}"
    echo -e "   Hostname:        ${GREEN}$CONTAINER_HOSTNAME${NC}"
    echo -e "   IP Address:      ${GREEN}$container_ip${NC}"
    echo -e "   Username:        ${GREEN}root${NC}"
    echo -e "   Password:        ${GREEN}$CONTAINER_PASSWORD${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}⚙️  Getting Started:${NC}"
    echo ""
    echo -e "  ${GREEN}1.${NC} Open your web browser"
    echo -e "     ${BLUE}http://${container_ip}:5000${NC}"
    echo ""
    echo -e "  ${GREEN}2.${NC} Browse current free games (no setup needed!)"
    echo ""
    echo -e "  ${GREEN}3.${NC} When ready, click ${BLUE}'Settings'${NC} to configure:"
    echo -e "     • Gmail app password: ${BLUE}zgqw lvns lpex qscv${NC}"
    echo -e "     • Add email recipients"
    echo -e "     • Test email delivery"
    echo ""
    echo -e "  ${GREEN}4.${NC} Enable automatic weekly checks:"
    echo -e "     ${BLUE}pct exec $CTID -- systemctl start free-game-checker${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Useful Commands:${NC}"
    echo ""
    echo -e "  Enter container:"
    echo -e "  ${BLUE}pct enter $CTID${NC}"
    echo ""
    echo -e "  View web service:"
    echo -e "  ${BLUE}pct exec $CTID -- systemctl status free-game-checker-web${NC}"
    echo ""
    echo -e "  View logs:"
    echo -e "  ${BLUE}pct exec $CTID -- tail -f /var/log/free-game-checker.log${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}💡 The web interface is ready to use NOW!${NC}"
    echo -e "${GREEN}   Browse games without any configuration!${NC}"
    echo ""
    echo -e "${GREEN}Happy gaming! 🎮${NC}"
    echo ""
}

###############################################################################
# Main Script
###############################################################################

print_header "Free Game Checker - Automated LXC Setup"

# Pre-flight checks
print_step "Running pre-flight checks..."
check_root
check_proxmox
print_success "Pre-flight checks passed"

# Detect CTID
if [ -n "$1" ]; then
    CTID=$1
    print_info "Using manually specified CTID: $CTID"
    if pct status $CTID &>/dev/null || qm status $CTID &>/dev/null; then
        print_error "CTID $CTID is already in use!"
        exit 1
    fi
else
    CTID=$(get_next_ctid)
    print_info "Auto-detected next available CTID: $CTID"
fi

# Show configuration
echo ""
print_info "Container Configuration:"
echo "  Name:        $CONTAINER_NAME"
echo "  Hostname:    $CONTAINER_HOSTNAME"
echo "  CTID:        $CTID"
echo "  CPU Cores:   $CPU_CORES"
echo "  RAM:         ${RAM}MB"
echo "  Swap:        ${SWAP}MB"
echo "  Disk:        ${DISK_SIZE}GB"
echo "  Storage:     $STORAGE"
echo "  Network:     $BRIDGE (DHCP)"
echo "  Password:    $CONTAINER_PASSWORD"
echo ""

# Confirmation
read -p "$(echo -e ${YELLOW}Do you want to proceed? [y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installation cancelled"
    exit 0
fi

# Execute installation
download_template
create_container
start_container
install_application

# Get IP and show final info
CONTAINER_IP=$(get_container_ip)

if [ -z "$CONTAINER_IP" ]; then
    print_error "Could not detect container IP automatically"
    print_info "Find it with: pct exec $CTID -- ip addr show"
    CONTAINER_IP="<CHECK_MANUALLY>"
fi

# Final information
print_final_info "$CONTAINER_IP"

# Save info to file
INFO_FILE="/root/free-game-checker-info-${CTID}.txt"
cat > $INFO_FILE << EOF
Free Game Checker - Container Information
==========================================

Container ID:    $CTID
Hostname:        $CONTAINER_HOSTNAME
IP Address:      $CONTAINER_IP
Username:        root
Password:        $CONTAINER_PASSWORD

Web Interface:   http://${CONTAINER_IP}:5000

Access URL in your browser to start using Free Game Checker!
No configuration needed to browse current free games.

Optional Configuration:
  Gmail:         freegamechecker@gmail.com
  App Password:  zgqw lvns lpex qscv

Container Specs:
  CPU Cores:     $CPU_CORES
  RAM:           ${RAM}MB
  Disk:          ${DISK_SIZE}GB
  Storage:       $STORAGE

Created:         $(date)
EOF

print_success "Container information saved to: $INFO_FILE"

exit 0

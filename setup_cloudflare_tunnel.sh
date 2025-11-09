#!/bin/bash
# Cloudflare Tunnel Setup Script for radio.cobe.dev
# Usage: ./setup_cloudflare_tunnel.sh [install|create|start|stop|status|logs|daemon]

set -e

DOMAIN="radio.cobe.dev"
TUNNEL_NAME="radio-stream"
LOCAL_SERVICE="https://localhost:5002"
CONFIG_DIR="$HOME/.cloudflared"
CONFIG_FILE="$CONFIG_DIR/config.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function install_cloudflared() {
    echo "Installing cloudflared..."
    
    # Check if already installed
    if command -v cloudflared &> /dev/null; then
        print_warning "cloudflared is already installed"
        cloudflared --version
        return
    fi
    
    # Download and install
    cd /tmp
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    
    if command -v cloudflared &> /dev/null; then
        print_success "cloudflared installed successfully"
        cloudflared --version
    else
        print_error "Installation failed"
        exit 1
    fi
}

function authenticate() {
    echo "Starting authentication..."
    echo ""
    print_warning "This will open your browser. Log in to Cloudflare and select 'cobe.dev'"
    echo ""
    read -p "Press Enter to continue..."
    
    cloudflared tunnel login
    
    if [ -f "$CONFIG_DIR/cert.pem" ]; then
        print_success "Authentication successful!"
        print_success "Certificate saved to $CONFIG_DIR/cert.pem"
    else
        print_error "Authentication failed - cert.pem not found"
        exit 1
    fi
}

function create_tunnel() {
    echo "Creating tunnel '$TUNNEL_NAME'..."
    
    # Create config directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"
    
    # Check if tunnel already exists
    if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
        print_warning "Tunnel '$TUNNEL_NAME' already exists"
        TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        echo "Tunnel ID: $TUNNEL_ID"
    else
        # Create new tunnel
        cloudflared tunnel create "$TUNNEL_NAME"
        TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
        print_success "Tunnel created successfully!"
        echo "Tunnel ID: $TUNNEL_ID"
    fi
    
    # Create config file
    echo "Creating configuration file..."
    
    CREDENTIALS_FILE="$CONFIG_DIR/$TUNNEL_ID.json"
    
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        print_error "Credentials file not found: $CREDENTIALS_FILE"
        print_warning "Run: ./setup_cloudflare_tunnel.sh auth"
        exit 1
    fi
    
    cat > "$CONFIG_FILE" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CREDENTIALS_FILE

ingress:
  - hostname: $DOMAIN
    service: $LOCAL_SERVICE
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF
    
    print_success "Configuration file created: $CONFIG_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Route DNS: cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN"
    echo "2. Start tunnel: ./setup_cloudflare_tunnel.sh start"
}

function route_dns() {
    echo "Routing DNS for $DOMAIN..."
    cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN"
    print_success "DNS routed successfully!"
    echo ""
    print_warning "DNS propagation may take a few minutes"
}

function start_tunnel() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Config file not found. Run: ./setup_cloudflare_tunnel.sh create"
        exit 1
    fi
    
    print_success "Starting tunnel..."
    echo ""
    echo "Tunnel will run in foreground. Press Ctrl+C to stop."
    echo "For background mode, use: ./setup_cloudflare_tunnel.sh daemon"
    echo ""
    
    cloudflared tunnel --config "$CONFIG_FILE" run
}

function install_daemon() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Config file not found. Run: ./setup_cloudflare_tunnel.sh create"
        exit 1
    fi
    
    echo "Installing cloudflared as systemd service..."
    
    # First, copy config to system location (where cloudflared expects it)
    echo "Copying config files to /etc/cloudflared/..."
    sudo mkdir -p /etc/cloudflared
    sudo cp "$CONFIG_FILE" /etc/cloudflared/config.yml
    sudo cp "$CONFIG_DIR"/*.json /etc/cloudflared/ 2>/dev/null || true
    
    print_success "Config files copied to /etc/cloudflared/"
    
    # Now install service (it will find the config in /etc/cloudflared/)
    sudo cloudflared service install
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable and start
    sudo systemctl enable cloudflared
    sudo systemctl start cloudflared
    
    sleep 2
    
    if sudo systemctl is-active --quiet cloudflared; then
        print_success "Tunnel service installed and started!"
        echo ""
        echo "Useful commands:"
        echo "  Status:  sudo systemctl status cloudflared"
        echo "  Logs:    sudo journalctl -u cloudflared -f"
        echo "  Stop:    sudo systemctl stop cloudflared"
        echo "  Restart: sudo systemctl restart cloudflared"
    else
        print_error "Service failed to start"
        echo ""
        echo "Checking logs:"
        sudo journalctl -u cloudflared -n 20
        exit 1
    fi
}

function stop_daemon() {
    echo "Stopping cloudflared service..."
    sudo systemctl stop cloudflared
    print_success "Service stopped"
}

function status_daemon() {
    sudo systemctl status cloudflared
}

function logs_daemon() {
    echo "Showing cloudflared logs (Ctrl+C to exit)..."
    sudo journalctl -u cloudflared -f
}

function restart_daemon() {
    echo "Restarting cloudflared service..."
    sudo systemctl restart cloudflared
    sleep 2
    if sudo systemctl is-active --quiet cloudflared; then
        print_success "Service restarted successfully"
    else
        print_error "Service failed to restart"
        sudo systemctl status cloudflared
    fi
}

function show_help() {
    echo "Cloudflare Tunnel Setup for radio.cobe.dev"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     - Install cloudflared"
    echo "  auth        - Authenticate with Cloudflare (opens browser)"
    echo "  create      - Create tunnel and config file"
    echo "  route       - Route DNS (creates CNAME record)"
    echo "  start       - Start tunnel in foreground"
    echo "  daemon      - Install and start as systemd service"
    echo "  stop        - Stop daemon service"
    echo "  restart     - Restart daemon service"
    echo "  status      - Show daemon status"
    echo "  logs        - Show daemon logs"
    echo ""
    echo "Quick setup (run in order):"
    echo "  1. $0 install"
    echo "  2. $0 auth"
    echo "  3. $0 create"
    echo "  4. $0 route"
    echo "  5. $0 daemon"
}

# Main script
case "${1:-help}" in
    install)
        install_cloudflared
        ;;
    auth)
        authenticate
        ;;
    create)
        create_tunnel
        ;;
    route)
        route_dns
        ;;
    start)
        start_tunnel
        ;;
    daemon)
        install_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        logs_daemon
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac


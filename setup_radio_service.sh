#!/bin/bash
# Radio Systemd Service Setup Script
# Usage: ./setup_radio_service.sh [install|uninstall|status|logs]

set -e

SERVICE_NAME="radio.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
WORK_DIR="/home/cobe-liu/Developing/fasthtml"
VENV_PYTHON="$WORK_DIR/.venv/bin/python"
USER="cobe-liu"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function check_requirements() {
    # Check Python venv exists
    if [ ! -f "$VENV_PYTHON" ]; then
        print_error "Python venv not found at: $VENV_PYTHON"
        echo "Create it with: python -m venv .venv"
        exit 1
    fi
    
    # Check radio.py exists
    if [ ! -f "$WORK_DIR/radio.py" ]; then
        print_error "radio.py not found in: $WORK_DIR"
        exit 1
    fi
    
    print_success "All requirements met"
}

function install_service() {
    echo "Installing radio.service..."
    
    check_requirements
    
    # Create service file
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Radio Streaming Server
After=network.target
Wants=cloudflared.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_PYTHON radio.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Service file created: $SERVICE_FILE"
    
    # Reload systemd
    sudo systemctl daemon-reload
    print_success "Systemd reloaded"
    
    # Enable service
    sudo systemctl enable "$SERVICE_NAME"
    print_success "Service enabled (will start on boot)"
    
    # Start service
    sudo systemctl start "$SERVICE_NAME"
    
    # Wait a moment for startup
    sleep 2
    
    # Check status
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service started successfully!"
        echo ""
        echo "Useful commands:"
        echo "  Status:  sudo systemctl status $SERVICE_NAME"
        echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
        echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
        echo "  Restart: sudo systemctl restart $SERVICE_NAME"
        echo ""
        echo "Test your radio:"
        echo "  Local:  curl -k https://localhost:5002/radio/info"
        echo "  Public: curl https://radio.cobe.dev/radio/info"
    else
        print_error "Service failed to start"
        echo ""
        echo "Check logs:"
        sudo journalctl -u "$SERVICE_NAME" -n 20
        exit 1
    fi
}

function uninstall_service() {
    echo "Uninstalling radio.service..."
    
    # Stop service
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
        print_success "Service stopped"
    fi
    
    # Disable service
    if sudo systemctl is-enabled --quiet "$SERVICE_NAME"; then
        sudo systemctl disable "$SERVICE_NAME"
        print_success "Service disabled"
    fi
    
    # Remove service file
    if [ -f "$SERVICE_FILE" ]; then
        sudo rm "$SERVICE_FILE"
        print_success "Service file removed"
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    print_success "Service uninstalled"
}

function show_status() {
    sudo systemctl status "$SERVICE_NAME"
}

function show_logs() {
    echo "Showing radio service logs (Ctrl+C to exit)..."
    sudo journalctl -u "$SERVICE_NAME" -f
}

function restart_service() {
    echo "Restarting radio service..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep 2
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service restarted successfully"
        show_status
    else
        print_error "Service failed to restart"
        show_logs
        exit 1
    fi
}

function show_help() {
    echo "Radio Service Setup Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     - Install and start radio.service"
    echo "  uninstall   - Stop and remove radio.service"
    echo "  status      - Show service status"
    echo "  logs        - Show service logs (live)"
    echo "  restart     - Restart the service"
    echo ""
    echo "After installation, your radio will:"
    echo "  - Start automatically on boot"
    echo "  - Restart if it crashes"
    echo "  - Run in the background"
    echo "  - Be accessible at https://radio.cobe.dev"
}

# Main script
case "${1:-help}" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    restart)
        restart_service
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


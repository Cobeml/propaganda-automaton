#!/bin/bash
# Helper script to add radio.local hostname to /etc/hosts
# Run this on CLIENT machines (not the server)

HOSTS_FILE="/etc/hosts"
HOSTNAME="radio.local"

# Get server IP from user
echo "Enter the radio server IP address:"
read SERVER_IP

if [ -z "$SERVER_IP" ]; then
    echo "❌ No IP address provided"
    exit 1
fi

# Check if entry already exists
if grep -q "$HOSTNAME" "$HOSTS_FILE"; then
    echo "⚠️  Entry for $HOSTNAME already exists in $HOSTS_FILE"
    echo "Current entry:"
    grep "$HOSTNAME" "$HOSTS_FILE"
    echo ""
    echo "Do you want to update it? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove old entry
        sudo sed -i "/$HOSTNAME/d" "$HOSTS_FILE"
    else
        echo "Cancelled."
        exit 0
    fi
fi

# Add new entry
echo "$SERVER_IP    $HOSTNAME" | sudo tee -a "$HOSTS_FILE" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Added $HOSTNAME -> $SERVER_IP to $HOSTS_FILE"
    echo ""
    echo "You can now access the radio at:"
    echo "  https://$HOSTNAME:5002"
    echo ""
    echo "Note: Browsers are more lenient with hostname-based certificates"
    echo "      than IP-based certificates."
else
    echo "❌ Failed to add entry. You may need to run with sudo."
    exit 1
fi


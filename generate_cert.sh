#!/bin/bash
# Generate SSL certificate with Subject Alternative Names for localhost and IP addresses

CERT_FILE="cert.pem"
KEY_FILE="key.pem"

# Backup existing certificates if they exist
if [ -f "$CERT_FILE" ] || [ -f "$KEY_FILE" ]; then
    echo "⚠️  Backing up existing certificates..."
    BACKUP_DIR="cert_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    [ -f "$CERT_FILE" ] && cp "$CERT_FILE" "$BACKUP_DIR/"
    [ -f "$KEY_FILE" ] && cp "$KEY_FILE" "$BACKUP_DIR/"
    echo "   Backed up to: $BACKUP_DIR/"
    echo ""
fi

# Get ALL local IP addresses (excluding loopback)
# This includes all network interfaces: local network, Docker, VPN (Tailscale), etc.
ALL_IPS=$(ip -4 addr show | grep "inet " | awk '{print $2}' | cut -d/ -f1 | grep -v "^127\.")

# Build IP list for certificate
echo "Generating SSL certificate for:"
echo "  - localhost"
echo "  - radio.local (recommended hostname)"
echo "  - 127.0.0.1"

# Start building openssl config file
cat > /tmp/ssl.conf << 'CONF_BASE'
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Organization
CN=localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = radio.local
DNS.4 = *.radio.local
IP.1 = 127.0.0.1
CONF_BASE

# Add all IP addresses to the config
IP_COUNT=1
for ip in $ALL_IPS; do
    echo "  - $ip"
    IP_COUNT=$((IP_COUNT + 1))
    echo "IP.${IP_COUNT} = ${ip}" >> /tmp/ssl.conf
done

echo ""

# Generate private key
openssl genrsa -out "$KEY_FILE" 2048

# Generate certificate with SANs
openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 -config /tmp/ssl.conf -extensions v3_req

# Cleanup
rm /tmp/ssl.conf

echo ""
echo "✅ Certificate generated successfully!"
echo "   Certificate: $CERT_FILE"
echo "   Private Key: $KEY_FILE"
echo ""
echo "📋 Certificate is valid for:"
openssl x509 -in "$CERT_FILE" -text -noout | grep -A 10 "Subject Alternative Name" | head -11
echo ""
echo "⚠️  IMPORTANT: Browser Security Warnings"
echo "   - Browsers will show a security warning for self-signed certificates"
echo "   - You must click 'Advanced' and 'Proceed anyway' (or similar)"
echo "   - This is normal for self-signed certificates"
echo ""
echo "💡 To use this certificate:"
echo "   1. Restart your radio server"
echo "   2. Access via any IP address listed above"
echo "   3. Accept the browser security warning"
echo ""
echo "📝 RECOMMENDED: Use hostname instead of IP address"
echo "   On client machines, add to /etc/hosts:"
echo "   <server-ip>    radio.local"
echo "   Then access: https://radio.local:5002"
echo "   (Browsers are more lenient with hostname-based certificates)"
echo ""
echo "   Or run: ./setup_hostname.sh on client machines"

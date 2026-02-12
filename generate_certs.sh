#!/bin/bash
# Generate SSL certificates for WarriorFit API

# Configuration
CERT_DIR="src/certs"
DAYS=365
KEY_SIZE=4096

# Server configuration
COUNTRY="BE"
STATE="Brussels"
LOCALITY="Brussels"
ORGANIZATION="WarriorFit"
ORG_UNIT="IT"
COMMON_NAME="warriorfit-api"

# Get server IP (you can override this)
SERVER_IP="${1:-78.21.255.210}"

echo "🔒 Generating SSL Certificates for WarriorFit API"
echo "=================================================="
echo "Certificate Directory: $CERT_DIR"
echo "Validity: $DAYS days"
echo "Key Size: $KEY_SIZE bits"
echo "Server IP: $SERVER_IP"
echo ""

# Create certs directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate certificate
openssl req -x509 -newkey rsa:$KEY_SIZE -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days $DAYS \
  -subj "/C=$COUNTRY/ST=$STATE/L=$LOCALITY/O=$ORGANIZATION/OU=$ORG_UNIT/CN=$COMMON_NAME" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,DNS:$COMMON_NAME,IP:127.0.0.1,IP:0.0.0.0,IP:$SERVER_IP"

# Set proper permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "Certificate Details:"
echo "-------------------"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -subject -issuer -dates
echo ""
echo "Subject Alternative Names:"
openssl x509 -in "$CERT_DIR/cert.pem" -noout -text | grep -A1 "Subject Alternative Name"
echo ""
echo "📁 Files created:"
echo "   $CERT_DIR/cert.pem (public certificate)"
echo "   $CERT_DIR/key.pem (private key)"
echo ""
echo "💡 Usage:"
echo "   # Default (78.21.255.210)"
echo "   ./generate_certs.sh"
echo ""
echo "   # Custom IP"
echo "   ./generate_certs.sh 192.168.1.100"

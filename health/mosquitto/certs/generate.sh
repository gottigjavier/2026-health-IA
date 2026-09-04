#!/usr/bin/env bash
# =============================================================================
# generate.sh — TLS certificate generation for Mosquitto MQTT broker
# =============================================================================
# Generates:
#   1. A self-signed Certificate Authority (CA)
#   2. A server certificate signed by the CA (for Mosquitto broker)
#   3. A client certificate for ESP8266 devices
#   4. A client certificate for Django backend
#
# Requirements: openssl
# Usage: chmod +x generate.sh && ./generate.sh
# =============================================================================
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")" && pwd)"
CA_DAYS=3650      # 10-year CA validity
CERT_DAYS=1825    # 5-year cert validity
KEY_SIZE=2048
DAYS_REMAINING=30 # Regenerate if certs expire within this many days

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Helpers ----------------------------------------------------------------

# Check if a certificate exists and is valid (not expiring soon)
cert_valid() {
    local cert="$1"
    [[ -f "$cert" ]] || return 1
    # openssl check below; if it fails the cert is invalid
    local expiry
    expiry=$(openssl x509 -enddate -noout -in "$cert" 2>/dev/null | cut -d= -f2)
    [[ -z "$expiry" ]] && return 1
    local expiry_epoch
    expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null) || return 1
    local now_epoch
    now_epoch=$(date +%s)
    local diff=$(( expiry_epoch - now_epoch ))
    (( diff > DAYS_REMAINING * 86400 ))
}

# --- Pre-flight checks ------------------------------------------------------

if ! command -v openssl &>/dev/null; then
    error "openssl not found. Install it and try again."
    exit 1
fi

info "Certificate directory: $CERT_DIR"

# --- 1. Certificate Authority (CA) ------------------------------------------

if cert_valid "$CERT_DIR/ca.crt"; then
    info "CA certificate already valid — skipping generation."
else
    info "Generating CA certificate..."
    openssl req -new -x509 \
        -days "$CA_DAYS" \
        -nodes \
        -keyout "$CERT_DIR/ca.key" \
        -out "$CERT_DIR/ca.crt" \
        -subj "/C=AR/ST=Buenos_Aires/L=CABA/O=HealthTodo/CN=HealthTodo-CA" \
        -sha256

    chmod 644 "$CERT_DIR/ca.key"       # 644 for container compatibility
    info "CA certificate created: ca.crt (valid ${CA_DAYS} days)"
fi

# --- 2. Server certificate (Mosquitto broker) --------------------------------

if cert_valid "$CERT_DIR/server.crt" && [[ -f "$CERT_DIR/server.key" ]]; then
    info "Server certificate already valid — skipping generation."
else
    info "Generating server certificate..."

    # Create a temporary OpenSSL config with SAN for the server cert
    SERVER_CNF=$(mktemp)
    cat > "$SERVER_CNF" <<EOF
[req]
default_bits       = ${KEY_SIZE}
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = v3_req

[dn]
C  = AR
ST = Buenos_Aires
L  = CABA
O  = HealthTodo
CN = mosquitto

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = mosquitto
DNS.2 = localhost
IP.1  = 127.0.0.1
IP.2  = 192.168.0.36
EOF

    # Generate server key + CSR
    openssl req -new \
        -nodes \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.csr" \
        -config "$SERVER_CNF"

    # Sign CSR with CA, including SAN extension
    openssl x509 -req \
        -in "$CERT_DIR/server.csr" \
        -CA "$CERT_DIR/ca.crt" \
        -CAkey "$CERT_DIR/ca.key" \
        -CAcreateserial \
        -out "$CERT_DIR/server.crt" \
        -days "$CERT_DAYS" \
        -sha256 \
        -extensions v3_req \
        -extfile "$SERVER_CNF"

    # Clean up temporary files
    rm -f "$CERT_DIR/server.csr" "$SERVER_CNF" "$CERT_DIR/ca.srl"

    chmod 644 "$CERT_DIR/server.key"   # 644 so container user can read (not 600 — owner-only breaks read-only mounts)
    chmod 644 "$CERT_DIR/server.crt"
    info "Server certificate created: server.crt (valid ${CERT_DAYS} days)"
fi

# --- 3. Client certificate — ESP8266 (room1) ---------------------------------

generate_client_cert() {
    local name="$1"
    local cn="$2"

    if cert_valid "$CERT_DIR/${name}.crt" && [[ -f "$CERT_DIR/${name}.key" ]]; then
        info "Client certificate '${name}' already valid — skipping."
        return
    fi

    info "Generating client certificate: ${name}..."

    openssl req -new \
        -nodes \
        -keyout "$CERT_DIR/${name}.key" \
        -out "$CERT_DIR/${name}.csr" \
        -subj "/C=AR/ST=Buenos_Aires/L=CABA/O=HealthTodo/CN=${cn}" \
        -sha256

    # Convert key to PKCS#1 (BEGIN RSA PRIVATE KEY) — required by ESP8266 BearSSL,
    # which cannot parse the default PKCS#8 (BEGIN PRIVATE KEY) output of openssl req.
    openssl rsa -in "$CERT_DIR/${name}.key" -traditional -out "$CERT_DIR/${name}.key" 2>/dev/null

    openssl x509 -req \
        -in "$CERT_DIR/${name}.csr" \
        -CA "$CERT_DIR/ca.crt" \
        -CAkey "$CERT_DIR/ca.key" \
        -CAcreateserial \
        -out "$CERT_DIR/${name}.crt" \
        -days "$CERT_DAYS" \
        -sha256

    rm -f "$CERT_DIR/${name}.csr" "$CERT_DIR/ca.srl"

    chmod 644 "$CERT_DIR/${name}.key"  # 644 for container compatibility
    chmod 644 "$CERT_DIR/${name}.crt"
    info "Client certificate created: ${name}.crt (valid ${CERT_DAYS} days)"
}

# ESP8266 client cert uses EC P-256 instead of RSA.
# WHY: BearSSL's RSA-2048 client-cert signing (br_rsa_i15_private / br_i15_modpow_opt)
# overflows the ~6KB BearSSL secondary stack during the mTLS handshake (CertificateVerify),
# causing a hard crash ("ctx: bearssl Stack overflow detected"). ECDSA P-256 signing uses
# far less stack, so it fits. The server + CA stay RSA; an EC client signed by an RSA CA
# is perfectly valid. EC is the standard choice for embedded mTLS (e.g. AWS IoT).
generate_client_ec_cert() {
    local name="$1"
    local cn="$2"

    if cert_valid "$CERT_DIR/${name}.crt" && [[ -f "$CERT_DIR/${name}.key" ]]; then
        info "Client EC certificate '${name}' already valid — skipping."
        return
    fi

    info "Generating client EC certificate: ${name}..."

    # Generate EC P-256 (prime256v1) private key. BearSSL expects the SEC1
    # "BEGIN EC PRIVATE KEY" format, which openssl ecparam produces directly.
    openssl ecparam -name prime256v1 -genkey -noout -out "$CERT_DIR/${name}.key"

    openssl req -new \
        -key "$CERT_DIR/${name}.key" \
        -out "$CERT_DIR/${name}.csr" \
        -subj "/C=AR/ST=Buenos_Aires/L=CABA/O=HealthTodo/CN=${cn}" \
        -sha256

    openssl x509 -req \
        -in "$CERT_DIR/${name}.csr" \
        -CA "$CERT_DIR/ca.crt" \
        -CAkey "$CERT_DIR/ca.key" \
        -CAcreateserial \
        -out "$CERT_DIR/${name}.crt" \
        -days "$CERT_DAYS" \
        -sha256

    rm -f "$CERT_DIR/${name}.csr" "$CERT_DIR/ca.srl"

    chmod 644 "$CERT_DIR/${name}.key"  # 644 for container compatibility
    chmod 644 "$CERT_DIR/${name}.crt"
    info "Client EC certificate created: ${name}.crt (EC P-256, valid ${CERT_DAYS} days)"
}

generate_client_ec_cert "client-esp-room1" "esp-room1"
generate_client_cert "client-django" "django-backend"

# --- Summary -----------------------------------------------------------------

echo ""
info "=== Certificate generation complete ==="
echo ""
ls -la "$CERT_DIR"/*.crt "$CERT_DIR"/*.key 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}'
echo ""
info "Files created in: $CERT_DIR"
echo ""

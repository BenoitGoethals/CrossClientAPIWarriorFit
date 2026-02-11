#!/bin/bash
# WarriorFit API Test Script using curl

API_URL="https://localhost:8555"
CERT_PATH="./src/certs/cert.pem"
API_KEY="warriorfit_cross_the_world"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Test 1: Get crosses with API Key
test_api_key_auth() {
    print_banner "TEST 1: API Key Authentication"
    print_info "GET /crosses with API Key"

    response=$(curl -s -w "\n%{http_code}" -X GET \
        "${API_URL}/crosses" \
        -H "X-API-Key: ${API_KEY}" \
        --cacert "${CERT_PATH}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "200" ]; then
        print_success "API Key authentication successful"
        echo "$body" | python3 -m json.tool | head -20
    else
        print_error "API Key authentication failed (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 2: OAuth2 login
test_oauth2_login() {
    print_banner "TEST 2: OAuth2 Login"

    read -p "Enter username: " username
    read -s -p "Enter password: " password
    echo ""

    print_info "POST /token (OAuth2 login)"

    response=$(curl -s -w "\n%{http_code}" -X POST \
        "${API_URL}/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${username}&password=${password}" \
        --cacert "${CERT_PATH}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "200" ]; then
        print_success "Login successful"
        echo "$body" | python3 -m json.tool

        # Extract access token
        ACCESS_TOKEN=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

        if [ ! -z "$ACCESS_TOKEN" ]; then
            print_success "Access token received"
            echo "Token: ${ACCESS_TOKEN:0:50}..."

            # Test with token
            print_info "Testing GET /crosses with OAuth2 token"
            response=$(curl -s -w "\n%{http_code}" -X GET \
                "${API_URL}/crosses" \
                -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                --cacert "${CERT_PATH}")

            http_code=$(echo "$response" | tail -n1)
            body=$(echo "$response" | sed '$d')

            if [ "$http_code" == "200" ]; then
                print_success "OAuth2 token authentication successful"
                echo "$body" | python3 -m json.tool | head -20
            else
                print_error "OAuth2 token authentication failed (HTTP $http_code)"
                echo "$body"
            fi
        fi
    else
        print_error "Login failed (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 3: Unauthorized access
test_unauthorized() {
    print_banner "TEST 3: Unauthorized Access"
    print_info "GET /crosses without authentication"

    response=$(curl -s -w "\n%{http_code}" -X GET \
        "${API_URL}/crosses" \
        --cacert "${CERT_PATH}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "401" ] || [ "$http_code" == "403" ]; then
        print_success "API correctly blocks unauthorized access (HTTP $http_code)"
        echo "$body"
    else
        print_error "Unexpected response (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 4: Get specific cross
test_get_cross() {
    print_banner "TEST 4: Get Specific Cross"

    read -p "Enter cross ID to retrieve: " cross_id

    print_info "GET /crosses/${cross_id} with API Key"

    response=$(curl -s -w "\n%{http_code}" -X GET \
        "${API_URL}/crosses/${cross_id}" \
        -H "X-API-Key: ${API_KEY}" \
        --cacert "${CERT_PATH}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" == "200" ]; then
        print_success "Cross retrieved successfully"
        echo "$body" | python3 -m json.tool
    else
        print_error "Failed to retrieve cross (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 5: Check SSL certificate
test_ssl_certificate() {
    print_banner "TEST 5: SSL Certificate Validation"
    print_info "Checking SSL certificate"

    openssl s_client -connect localhost:8555 -showcerts < /dev/null 2>/dev/null | \
        openssl x509 -noout -text | \
        grep -E "(Subject:|Issuer:|Not Before|Not After|DNS:|IP Address:)"

    if [ $? -eq 0 ]; then
        print_success "SSL certificate is valid"
    else
        print_error "Failed to validate SSL certificate"
    fi
}

# Main menu
main_menu() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║              WarriorFit API Test Script (curl)                       ║
║                                                                      ║
║  Tests authentication and role-based access control                 ║
╚══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    while true; do
        echo ""
        echo "Select test:"
        echo "  1. Test API Key authentication"
        echo "  2. Test OAuth2 login"
        echo "  3. Test unauthorized access"
        echo "  4. Get specific cross"
        echo "  5. Check SSL certificate"
        echo "  6. Run all tests"
        echo "  0. Exit"
        echo ""
        read -p "Enter choice: " choice

        case $choice in
            1) test_api_key_auth ;;
            2) test_oauth2_login ;;
            3) test_unauthorized ;;
            4) test_get_cross ;;
            5) test_ssl_certificate ;;
            6)
                test_api_key_auth
                test_unauthorized
                test_ssl_certificate
                echo ""
                read -p "Run OAuth2 test? (y/n): " run_oauth
                if [ "$run_oauth" == "y" ]; then
                    test_oauth2_login
                fi
                ;;
            0)
                echo -e "\n${GREEN}👋 Goodbye!${NC}\n"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac
    done
}

# Run main menu
main_menu

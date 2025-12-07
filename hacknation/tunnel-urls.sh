#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Cloudflare Tunnel URLs:${NC}"
echo ""

# Get backend tunnel URL
BACKEND_URL=$(docker logs tunnel-backend 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
if [ -n "$BACKEND_URL" ]; then
    echo -e "Backend API:  ${BLUE}$BACKEND_URL${NC}"
else
    echo -e "Backend API:  (not running)"
fi

# Get frontend tunnel URL
FRONTEND_URL=$(docker logs tunnel-frontend 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
if [ -n "$FRONTEND_URL" ]; then
    echo -e "Frontend:     ${BLUE}$FRONTEND_URL${NC}"
else
    echo -e "Frontend:     (not running)"
fi

echo ""


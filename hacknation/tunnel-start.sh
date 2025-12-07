#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ZUS Accident Notification Tool       ${NC}"
echo -e "${BLUE}  Cloudflare Tunnel Deployment         ${NC}"
echo -e "${BLUE}  (No account required!)               ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${GREEN}Step 1: Starting backend and tunnel...${NC}"
docker compose up -d backend tunnel-backend

echo -e "${YELLOW}Waiting for Cloudflare tunnel to be established...${NC}"
sleep 8

# Get the backend tunnel URL from container logs
echo -e "${GREEN}Step 2: Getting backend tunnel URL...${NC}"
BACKEND_URL=""
for i in {1..10}; do
    BACKEND_URL=$(docker logs tunnel-backend 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
    if [ -n "$BACKEND_URL" ]; then
        break
    fi
    echo -e "${YELLOW}  Waiting for tunnel... (attempt $i/10)${NC}"
    sleep 2
done

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}Error: Could not get backend tunnel URL${NC}"
    echo -e "Check logs: docker compose logs tunnel-backend"
    exit 1
fi

echo -e "${GREEN}Backend URL: ${BLUE}$BACKEND_URL${NC}"

echo -e "${GREEN}Step 3: Starting frontend with backend URL...${NC}"
REACT_APP_API_URL=$BACKEND_URL docker compose up -d frontend tunnel-frontend

echo -e "${YELLOW}Waiting for frontend tunnel...${NC}"
sleep 8

# Get the frontend tunnel URL
FRONTEND_URL=""
for i in {1..10}; do
    FRONTEND_URL=$(docker logs tunnel-frontend 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
    if [ -n "$FRONTEND_URL" ]; then
        break
    fi
    echo -e "${YELLOW}  Waiting for tunnel... (attempt $i/10)${NC}"
    sleep 2
done

if [ -z "$FRONTEND_URL" ]; then
    echo -e "${RED}Warning: Could not get frontend tunnel URL${NC}"
    echo -e "Check logs: docker compose logs tunnel-frontend"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All services are running!            ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Frontend URL:${NC}     $FRONTEND_URL"
echo -e "${BLUE}Backend API URL:${NC}  $BACKEND_URL"
echo ""
echo -e "${YELLOW}To check URLs anytime:${NC}"
echo -e "  ./tunnel-urls.sh"
echo ""
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  docker compose down"
echo ""


#!/bin/bash

# --#-- Quick Start Script for Phase 7 Testing
# This script starts all required services

set -e

echo "=============================================="
echo "  Phase 7 Quick Start"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .env_digital_wallet/bin/activate
fi

# Check Redis
echo -e "${BLUE}Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
    echo -e "${GREEN}✅ Redis started${NC}"
fi

echo ""
echo "=============================================="
echo "  Starting Services"
echo "=============================================="
echo ""

# Start Celery in background
echo -e "${BLUE}Starting Celery worker in background...${NC}"
DJANGO_SETTINGS_MODULE=core.settings.dev celery -A core worker -l info > /tmp/celery.log 2>&1 &
CELERY_PID=$!
echo -e "${GREEN}✅ Celery started (PID: $CELERY_PID)${NC}"
echo "   Logs: /tmp/celery.log"
echo ""

# Start Django server
echo -e "${BLUE}Starting Django server...${NC}"
echo -e "${GREEN}✅ Server will start at: http://localhost:8500${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

python manage.py runserver 8500 --settings=core.settings.dev

# Cleanup on exit
trap "echo ''; echo 'Stopping Celery...'; kill $CELERY_PID 2>/dev/null; echo 'Done.'" EXIT

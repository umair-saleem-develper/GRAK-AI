#!/bin/bash
set -e

# ANSI Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting Sprint 1 Verification Protocol...${NC}\n"

# Ensure docker is running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[FAIL] Docker is not installed on this machine.${NC}"
    exit 1
fi

echo -e "${YELLOW}1. Starting Docker Containers...${NC}"
docker compose up -d
echo -e "${GREEN}[PASS] Docker compose executed.${NC}\n"

echo -e "${YELLOW}Waiting for backend to become healthy (max 30s)...${NC}"
for i in {1..30}; do
  if curl -s http://localhost:8001/api/health > /dev/null; then
    break
  fi
  sleep 1
done

# 1. API Health Check
echo -e "${YELLOW}2. Verifying API Health...${NC}"
HEALTH=$(curl -s http://localhost:8001/api/health | grep '"success": true')
if [ -n "$HEALTH" ]; then
    echo -e "${GREEN}[PASS] Backend API is running and returns standardized JSON format.${NC}\n"
else
    echo -e "${RED}[FAIL] Backend API is unreachable or invalid format.${NC}\n"
fi

# 2. Database Connection Check
echo -e "${YELLOW}3. Checking PostgreSQL Database Connection...${NC}"
DB_CHECK=$(docker exec omniai_db pg_isready -U admin -d omniai_db)
if echo "$DB_CHECK" | grep -q "accepting connections"; then
    echo -e "${GREEN}[PASS] PostgreSQL is ready and accepting connections.${NC}\n"
else
    echo -e "${RED}[FAIL] PostgreSQL is not ready.${NC}\n"
fi

# 3. Redis Connection Check
echo -e "${YELLOW}4. Checking Redis Connection...${NC}"
REDIS_CHECK=$(docker exec omniai_redis redis-cli ping)
if [ "$REDIS_CHECK" = "PONG" ]; then
    echo -e "${GREEN}[PASS] Redis is ready and responding.${NC}\n"
else
    echo -e "${RED}[FAIL] Redis is not responding.${NC}\n"
fi

# 4. Alembic Migration Check
echo -e "${YELLOW}5. Verifying Alembic Migrations...${NC}"
ALEMBIC_CHECK=$(docker exec omniai_backend alembic current)
if echo "$ALEMBIC_CHECK" | grep -q "(head)"; then
    echo -e "${GREEN}[PASS] Alembic migrations are up to date (head).${NC}\n"
else
    echo -e "${RED}[FAIL] Alembic migrations are pending or failed.${NC}\n"
fi

# 5. Table Existence Check
echo -e "${YELLOW}6. Verifying Database Tables...${NC}"
TABLES=$(docker exec omniai_db psql -U admin -d omniai_db -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public';")
if echo "$TABLES" | grep -q "users" && echo "$TABLES" | grep -q "conversations" && echo "$TABLES" | grep -q "messages" && echo "$TABLES" | grep -q "alembic_version"; then
    echo -e "${GREEN}[PASS] All required tables exist (users, conversations, messages, alembic_version).${NC}\n"
else
    echo -e "${RED}[FAIL] Missing required tables in database schema.${NC}\n"
fi

# 6. JWT Authentication & Data Isolation Check
echo -e "${YELLOW}7. Verifying JWT Security and Data Isolation...${NC}"
# Register a dummy user
REGISTER=$(curl -s -X POST http://localhost:8001/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"sprint1_verify@example.com", "password":"password123"}')

# Login to get JWT
LOGIN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"sprint1_verify@example.com", "password":"password123"}')
  
TOKEN=$(echo $LOGIN | grep -o '"access_token": "[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}[PASS] JWT generated successfully.${NC}"
    
    # Try fetching with invalid token
    INVALID_FETCH=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid_token" http://localhost:8001/api/conversations/)
    if [ "$INVALID_FETCH" = "401" ]; then
        echo -e "${GREEN}[PASS] API rejected invalid JWT with 401.${NC}"
    else
        echo -e "${RED}[FAIL] API accepted invalid JWT or returned wrong code ($INVALID_FETCH).${NC}"
    fi

    # Try fetching with missing token
    MISSING_FETCH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/conversations/)
    if [ "$MISSING_FETCH" = "401" ]; then
        echo -e "${GREEN}[PASS] API rejected missing JWT with 401.${NC}\n"
    else
        echo -e "${RED}[FAIL] API accepted missing JWT or returned wrong code ($MISSING_FETCH).${NC}\n"
    fi

else
    echo -e "${RED}[FAIL] Failed to generate JWT token.${NC}\n"
fi

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Sprint 1 Verification Complete!${NC}"
echo -e "${GREEN}==========================================${NC}"

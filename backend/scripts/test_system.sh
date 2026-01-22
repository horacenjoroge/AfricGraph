#!/usr/bin/env bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 AfricGraph System Testing Script${NC}"
echo "=================================="
echo ""

# Configuration
API_URL="http://localhost:8000"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Check if API is running
echo -e "${YELLOW}1. Checking if API is running...${NC}"
if curl -s -f "${API_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ API is running${NC}"
else
    echo -e "${RED}❌ API is not running. Please start it first:${NC}"
    echo "   cd backend && source venv/bin/activate && uvicorn src.api.main:app --reload"
    exit 1
fi

# Test health endpoint
echo ""
echo -e "${YELLOW}2. Testing health endpoint...${NC}"
response=$(curl -s "${API_URL}/health")
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$response"
fi

# Test business search
echo ""
echo -e "${YELLOW}3. Testing business search endpoint...${NC}"
response=$(curl -s "${API_URL}/api/v1/businesses/search?limit=5")
if echo "$response" | grep -q "businesses"; then
    echo -e "${GREEN}✅ Business search works${NC}"
    echo "$response" | jq '.businesses | length' 2>/dev/null || echo "Found businesses"
else
    echo -e "${RED}❌ Business search failed${NC}"
    echo "$response"
fi

# Test business creation
echo ""
echo -e "${YELLOW}4. Testing business creation...${NC}"
test_business='{
  "id": "TEST001",
  "name": "Test Business",
  "sector": "Technology",
  "registration_number": "TEST123"
}'
response=$(curl -s -X POST "${API_URL}/api/v1/businesses" \
  -H "Content-Type: application/json" \
  -d "$test_business")
if echo "$response" | grep -q "TEST001"; then
    echo -e "${GREEN}✅ Business creation works${NC}"
else
    echo -e "${YELLOW}⚠️  Business creation response:${NC}"
    echo "$response"
fi

# Test business retrieval
echo ""
echo -e "${YELLOW}5. Testing business retrieval...${NC}"
response=$(curl -s "${API_URL}/api/v1/businesses/TEST001")
if echo "$response" | grep -q "TEST001"; then
    echo -e "${GREEN}✅ Business retrieval works${NC}"
else
    echo -e "${RED}❌ Business retrieval failed${NC}"
    echo "$response"
fi

# Test audit logs
echo ""
echo -e "${YELLOW}6. Testing audit logs endpoint...${NC}"
response=$(curl -s "${API_URL}/api/v1/audit?limit=5")
if echo "$response" | grep -q "logs"; then
    echo -e "${GREEN}✅ Audit logs endpoint works${NC}"
else
    echo -e "${YELLOW}⚠️  Audit logs response:${NC}"
    echo "$response" | head -20
fi

# Test risk endpoint
echo ""
echo -e "${YELLOW}7. Testing risk assessment endpoint...${NC}"
response=$(curl -s "${API_URL}/api/v1/risk/TEST001" 2>&1)
status_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/risk/TEST001")
if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Risk assessment works${NC}"
elif [ "$status_code" = "404" ]; then
    echo -e "${YELLOW}⚠️  Risk assessment endpoint returned 404 (may need data)${NC}"
else
    echo -e "${YELLOW}⚠️  Risk assessment status: $status_code${NC}"
fi

# Test graph endpoint
echo ""
echo -e "${YELLOW}8. Testing graph traversal endpoint...${NC}"
response=$(curl -s "${API_URL}/api/v1/graph/subgraph/TEST001?max_hops=1" 2>&1)
status_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/graph/subgraph/TEST001?max_hops=1")
if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Graph traversal works${NC}"
elif [ "$status_code" = "404" ]; then
    echo -e "${YELLOW}⚠️  Graph endpoint returned 404 (business may not exist)${NC}"
else
    echo -e "${YELLOW}⚠️  Graph traversal status: $status_code${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=================================="
echo "✅ System testing completed!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run seed data script: python backend/scripts/seed_data.py"
echo "2. Test the frontend at: http://localhost:3000"
echo "3. Check API docs at: ${API_URL}/docs"

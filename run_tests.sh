#!/bin/bash
# Test runner script for Job Apply Tool

set -e

echo "======================================"
echo "Job Apply Tool - Test Suite"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio
fi

# Create __init__.py if missing
if [ ! -f "backend/tests/__init__.py" ]; then
    touch backend/tests/__init__.py
fi

echo -e "${YELLOW}Running Phase 5 AI Integration Tests...${NC}"
echo "--------------------------------------"
python -m pytest backend/tests/test_ai_integration.py -v --tb=short
PHASE5_RESULT=$?

echo ""
echo -e "${YELLOW}Running Phase 6 API Endpoint Tests...${NC}"
echo "--------------------------------------"
python -m pytest backend/tests/test_api_endpoints.py -v --tb=short
PHASE6_RESULT=$?

echo ""
echo "======================================"
echo "Test Results Summary"
echo "======================================"

if [ $PHASE5_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 5 Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Phase 5 Tests: FAILED${NC}"
fi

if [ $PHASE6_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 6 Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Phase 6 Tests: FAILED${NC}"
fi

echo ""

# Exit with failure if any test suite failed
if [ $PHASE5_RESULT -ne 0 ] || [ $PHASE6_RESULT -ne 0 ]; then
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi

echo -e "${GREEN}All tests passed successfully!${NC}"
exit 0

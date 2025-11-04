#!/bin/bash
# Quick test runner script for listen project

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running listen tests...${NC}\n"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Parse arguments
case "${1:-all}" in
    "config")
        echo -e "${GREEN}Running config tests...${NC}"
        pytest test_config.py -v
        ;;
    "listen")
        echo -e "${GREEN}Running listen tests...${NC}"
        pytest test_listen.py -v
        ;;
    "coverage")
        echo -e "${GREEN}Running all tests with coverage...${NC}"
        pytest --cov=. --cov-report=term --cov-report=html
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo -e "${GREEN}Running quick tests (no output)...${NC}"
        pytest -q
        ;;
    "all"|*)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest -v
        ;;
esac

echo -e "\n${GREEN}✓ Tests completed${NC}"

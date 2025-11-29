#!/bin/bash

# Genesis Pipeline Health Check Script
# Verifies all services are running correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "Genesis Pipeline - Health Check"
echo "========================================="
echo ""

# Function to check if service is running
check_service() {
    local service=$1
    local container=$2
    
    if docker ps | grep -q "$container"; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is NOT running"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is responding"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT responding"
        return 1
    fi
}

# Function to check file exists
check_file() {
    local name=$1
    local file=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $name exists"
        return 0
    else
        echo -e "${RED}✗${NC} $name is MISSING"
        return 1
    fi
}

# Check Docker is running
echo -e "${BLUE}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Check containers
echo -e "${BLUE}Checking Containers...${NC}"
check_service "Genesis App" "genesis-pipeline"
check_service "Loki" "genesis-loki"
check_service "Promtail" "genesis-promtail"
check_service "Grafana" "genesis-grafana"
echo ""

# Check endpoints
echo -e "${BLUE}Checking Endpoints...${NC}"
check_endpoint "Loki Ready" "http://localhost:3100/ready"
check_endpoint "Loki Metrics" "http://localhost:3100/metrics"
check_endpoint "Grafana" "http://localhost:3000"
echo ""

# Check configuration files
echo -e "${BLUE}Checking Configuration Files...${NC}"
check_file "Loki Config" "config/loki-config.yaml"
check_file "Promtail Config" "config/promtail-config.yaml"
check_file "Grafana Datasources" "config/grafana-datasources.yaml"
check_file "Grafana Dashboards" "config/grafana-dashboards.yaml"
echo ""

# Check source files
echo -e "${BLUE}Checking Source Files...${NC}"
check_file "State Module" "src/state.py"
check_file "Nodes Module" "src/nodes.py"
check_file "Graph Module" "src/graph.py"
check_file "Logger Config" "src/logger_config.py"
check_file "Main Script" "main.py"
echo ""

# Check environment
echo -e "${BLUE}Checking Environment...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "${GREEN}✓${NC} OPENAI_API_KEY is configured"
    elif grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        echo -e "${YELLOW}⚠${NC} OPENAI_API_KEY needs to be updated"
    else
        echo -e "${RED}✗${NC} OPENAI_API_KEY is missing"
    fi
else
    echo -e "${RED}✗${NC} .env file is missing"
fi
echo ""

# Check directories
echo -e "${BLUE}Checking Directories...${NC}"
for dir in output logs config src; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/ directory exists"
    else
        echo -e "${RED}✗${NC} $dir/ directory is missing"
    fi
done
echo ""

# Check logs
echo -e "${BLUE}Checking Application Logs...${NC}"
if docker ps | grep -q "genesis-pipeline"; then
    # Check for recent errors
    error_count=$(docker logs genesis-pipeline 2>&1 | grep -i "error" | wc -l)
    
    if [ "$error_count" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No errors in application logs"
    else
        echo -e "${YELLOW}⚠${NC} Found $error_count error(s) in logs"
        echo -e "${YELLOW}  Run: docker-compose logs genesis-app${NC}"
    fi
    
    # Check if pipeline has run
    if docker logs genesis-pipeline 2>&1 | grep -q "GENESIS PIPELINE COMPLETED"; then
        echo -e "${GREEN}✓${NC} Pipeline has completed successfully"
    elif docker logs genesis-pipeline 2>&1 | grep -q "GENESIS PIPELINE INITIATED"; then
        echo -e "${BLUE}ℹ${NC} Pipeline is running or has run"
    else
        echo -e "${YELLOW}⚠${NC} Pipeline may not have run yet"
    fi
else
    echo -e "${YELLOW}⚠${NC} Application container is not running"
fi
echo ""

# Check output files
echo -e "${BLUE}Checking Output Files...${NC}"
if [ -d "output" ] && [ "$(ls -A output 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} Output directory has files:"
    ls -1 output/ | head -5 | while read file; do
        echo "  - $file"
    done
    file_count=$(find output -type f | wc -l)
    echo "  (Total: $file_count files)"
else
    echo -e "${YELLOW}⚠${NC} Output directory is empty (pipeline may not have run)"
fi
echo ""

# Docker resource usage
echo -e "${BLUE}Checking Resource Usage...${NC}"
echo "Container Statistics:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep genesis || echo "No Genesis containers found"
echo ""

# Network check
echo -e "${BLUE}Checking Network...${NC}"
if docker network ls | grep -q "genesis-pipeline_genesis-network"; then
    echo -e "${GREEN}✓${NC} Docker network exists"
    container_count=$(docker network inspect genesis-pipeline_genesis-network | grep -c "genesis-")
    echo "  Connected containers: $container_count"
else
    echo -e "${RED}✗${NC} Docker network is missing"
fi
echo ""

# Summary
echo "========================================="
echo "Health Check Summary"
echo "========================================="

# Count checks
services_ok=$(docker ps | grep -c "genesis-" || true)
total_services=4

if [ "$services_ok" -eq "$total_services" ]; then
    echo -e "${GREEN}All systems operational!${NC}"
    echo ""
    echo "Access Points:"
    echo "  - Grafana: http://localhost:3000 (admin/genesis2024)"
    echo "  - Loki: http://localhost:3100"
    echo ""
    echo "Quick Commands:"
    echo "  - View logs: docker-compose logs -f genesis-app"
    echo "  - Restart: docker-compose restart genesis-app"
    echo "  - Stop all: docker-compose down"
else
    echo -e "${YELLOW}Some services need attention${NC}"
    echo ""
    echo "Running services: $services_ok/$total_services"
    echo ""
    echo "Try:"
    echo "  docker-compose up -d     # Start services"
    echo "  docker-compose ps        # Check status"
    echo "  docker-compose logs      # View logs"
fi

echo ""
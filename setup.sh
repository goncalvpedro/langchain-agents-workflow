#!/bin/bash

# Genesis Pipeline Setup Script
# This script prepares the environment for running the Genesis Pipeline

set -e

echo "========================================="
echo "Genesis Pipeline - Setup Script"
echo "========================================="
echo ""

# Function to print colored output
print_success() {
    echo -e "\033[0;32m✓ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m✗ $1\033[0m"
}

print_info() {
    echo -e "\033[0;34mℹ $1\033[0m"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose is installed"

# Create necessary directories
print_info "Creating required directories..."
mkdir -p config/dashboards
mkdir -p logs
mkdir -p output
mkdir -p src

print_success "Directories created"

# Check if .env file exists
if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created"
        print_error "IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
        echo ""
        echo "Run: nano .env"
        echo "or: vim .env"
        echo ""
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# Validate .env has OPENAI_API_KEY
if [ -f .env ]; then
    if grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        print_error "Please update OPENAI_API_KEY in .env file before running"
        exit 1
    elif grep -q "OPENAI_API_KEY=" .env; then
        print_success "OPENAI_API_KEY is configured"
    else
        print_error "OPENAI_API_KEY not found in .env"
        exit 1
    fi
fi

# Check if config files exist
print_info "Checking configuration files..."

required_configs=(
    "config/loki-config.yaml"
    "config/promtail-config.yaml"
    "config/grafana-datasources.yaml"
    "config/grafana-dashboards.yaml"
)

all_configs_exist=true
for config in "${required_configs[@]}"; do
    if [ ! -f "$config" ]; then
        print_error "Missing: $config"
        all_configs_exist=false
    fi
done

if [ "$all_configs_exist" = true ]; then
    print_success "All configuration files present"
else
    print_error "Some configuration files are missing. Please create them."
    exit 1
fi

# Check if source files exist
print_info "Checking source files..."

required_sources=(
    "src/state.py"
    "src/nodes.py"
    "src/graph.py"
    "src/logger_config.py"
    "main.py"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
)

all_sources_exist=true
for source in "${required_sources[@]}"; do
    if [ ! -f "$source" ]; then
        print_error "Missing: $source"
        all_sources_exist=false
    fi
done

if [ "$all_sources_exist" = true ]; then
    print_success "All source files present"
else
    print_error "Some source files are missing. Please create them."
    exit 1
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
print_info "Next steps:"
echo "  1. Ensure your OPENAI_API_KEY is set in .env"
echo "  2. Run: docker-compose up -d"
echo "  3. Access Grafana at http://localhost:3000"
echo "     Login: admin / genesis2024"
echo ""
print_success "Ready to launch Genesis Pipeline!"
echo ""
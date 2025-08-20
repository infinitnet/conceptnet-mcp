#!/bin/bash

# ConceptNet MCP Server - Cloudflare Workers Deployment Script
# This script automates the deployment process to Cloudflare Workers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-development}"
DEPLOY_MODE="${2:-deploy}"

echo -e "${BLUE}🚀 ConceptNet MCP Server - Cloudflare Workers Deployment${NC}"
echo "=================================================="
echo "Environment: $ENVIRONMENT"
echo "Mode: $DEPLOY_MODE"
echo "Script Directory: $SCRIPT_DIR"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}📋 Checking prerequisites...${NC}"
    
    # Check if wrangler is installed
    if ! command -v wrangler &> /dev/null; then
        echo -e "${RED}❌ Wrangler CLI is not installed${NC}"
        echo "Install it with: npm install -g wrangler"
        exit 1
    fi
    echo -e "${GREEN}✅ Wrangler CLI found${NC}"
    
    # Check if logged in to Cloudflare
    if ! wrangler whoami &> /dev/null; then
        echo -e "${RED}❌ Not logged in to Cloudflare${NC}"
        echo "Login with: wrangler login"
        exit 1
    fi
    echo -e "${GREEN}✅ Cloudflare authentication verified${NC}"
    
    # Check if wrangler.toml exists
    if [ ! -f "$SCRIPT_DIR/wrangler.toml" ]; then
        echo -e "${RED}❌ wrangler.toml not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ wrangler.toml found${NC}"
    
    # Check if main.py exists
    if [ ! -f "$SCRIPT_DIR/src/main.py" ]; then
        echo -e "${RED}❌ src/main.py not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ main.py found${NC}"
    
    # Check if parent conceptnet-mcp package exists
    if [ ! -f "$PROJECT_ROOT/src/conceptnet_mcp/server.py" ]; then
        echo -e "${RED}❌ Parent ConceptNet MCP package not found${NC}"
        echo "Make sure you're running this from within the conceptnet-mcp project"
        exit 1
    fi
    echo -e "${GREEN}✅ ConceptNet MCP source found${NC}"
    
    echo ""
}

# Function to validate configuration
validate_config() {
    echo -e "${BLUE}🔍 Validating configuration...${NC}"
    
    # Check wrangler.toml syntax
    if ! wrangler validate; then
        echo -e "${RED}❌ wrangler.toml validation failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ wrangler.toml is valid${NC}"
    
    # Check for required environment variables in wrangler.toml
    local required_vars=("CONCEPTNET_API_URL" "MCP_SERVER_NAME")
    for var in "${required_vars[@]}"; do
        if ! grep -q "$var" wrangler.toml; then
            echo -e "${YELLOW}⚠️  Warning: $var not found in wrangler.toml${NC}"
        fi
    done
    
    echo ""
}

# Function to run tests (if available)
run_tests() {
    echo -e "${BLUE}🧪 Running tests...${NC}"
    
    # Check if there are any tests to run
    if [ -f "$PROJECT_ROOT/run_tests.py" ]; then
        echo "Running ConceptNet MCP tests..."
        cd "$PROJECT_ROOT"
        python run_tests.py || {
            echo -e "${YELLOW}⚠️  Tests failed, but continuing with deployment${NC}"
        }
        cd "$SCRIPT_DIR"
    else
        echo -e "${YELLOW}⚠️  No tests found, skipping test phase${NC}"
    fi
    
    echo ""
}

# Function to deploy
deploy() {
    echo -e "${BLUE}🚢 Deploying to Cloudflare Workers...${NC}"
    
    case $DEPLOY_MODE in
        "dev"|"development")
            echo "Starting development server..."
            wrangler dev --env development
            ;;
        "deploy")
            echo "Deploying to $ENVIRONMENT environment..."
            if [ "$ENVIRONMENT" = "production" ]; then
                echo -e "${YELLOW}⚠️  Deploying to PRODUCTION environment${NC}"
                read -p "Are you sure? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo "Deployment cancelled"
                    exit 1
                fi
            fi
            
            wrangler deploy --env "$ENVIRONMENT"
            ;;
        "publish")
            echo "Publishing to production..."
            wrangler deploy --env production
            ;;
        *)
            echo -e "${RED}❌ Unknown deploy mode: $DEPLOY_MODE${NC}"
            echo "Available modes: dev, deploy, publish"
            exit 1
            ;;
    esac
}

# Function to show post-deployment info
show_post_deployment_info() {
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo "=================================================="
    
    # Get the worker URL
    local worker_name=$(grep "name = " wrangler.toml | sed 's/name = "\(.*\)"/\1/')
    echo -e "${BLUE}Worker Name:${NC} $worker_name"
    
    # Show available endpoints
    echo -e "${BLUE}Available Endpoints:${NC}"
    echo "  SSE Transport: https://$worker_name.your-subdomain.workers.dev/sse"
    echo "  MCP Transport: https://$worker_name.your-subdomain.workers.dev/mcp"
    
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Test the deployment with: curl https://$worker_name.your-subdomain.workers.dev/mcp"
    echo "2. Monitor logs with: wrangler tail --env $ENVIRONMENT"
    echo "3. Check metrics in the Cloudflare dashboard"
    
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs: wrangler tail --env $ENVIRONMENT"
    echo "  View deployments: wrangler deployments list"
    echo "  Rollback: wrangler rollback [deployment-id]"
    echo "  Delete worker: wrangler delete"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [mode]"
    echo ""
    echo "Environments:"
    echo "  development (default) - Deploy to development environment"
    echo "  production           - Deploy to production environment"
    echo ""
    echo "Modes:"
    echo "  deploy (default)     - Deploy the worker"
    echo "  dev                  - Start development server"
    echo "  publish              - Publish to production"
    echo ""
    echo "Examples:"
    echo "  $0                   # Deploy to development"
    echo "  $0 production deploy # Deploy to production"
    echo "  $0 development dev   # Start development server"
}

# Main execution
main() {
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Handle help flag
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        exit 0
    fi
    
    # Validate environment parameter
    if [ "$ENVIRONMENT" != "development" ] && [ "$ENVIRONMENT" != "production" ]; then
        echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
        echo "Valid environments: development, production"
        exit 1
    fi
    
    # Run deployment steps
    check_prerequisites
    validate_config
    
    # Only run tests for actual deployment, not dev mode
    if [ "$DEPLOY_MODE" != "dev" ]; then
        run_tests
    fi
    
    deploy
    
    # Only show post-deployment info for actual deployments
    if [ "$DEPLOY_MODE" != "dev" ]; then
        show_post_deployment_info
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 130' INT

# Run main function
main "$@"
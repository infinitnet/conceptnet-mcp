# Installation Guide

This guide covers installation and setup of the ConceptNet MCP Server.

## Requirements

- Python 3.10 or higher
- pip package manager
- Git

## Installation

### Install from Source

```bash
# Clone the repository
git clone https://github.com/infinitnet/conceptnet-mcp.git
cd conceptnet-mcp

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

## Verification

Verify the installation by running:

```bash
# Check if the server can start
python -m conceptnet_mcp.server --help

# Test basic functionality
python -c "import conceptnet_mcp; print('Installation successful!')"
```

## Configuration

### Environment Variables

The server can be configured using environment variables:

```bash
# ConceptNet API settings
export CONCEPTNET_API_BASE_URL=https://api.conceptnet.io
export CONCEPTNET_API_VERSION=5.7

# Server settings
export MCP_SERVER_HOST=localhost
export MCP_SERVER_PORT=3000
export LOG_LEVEL=INFO

# Rate limiting (requests per period)
export CONCEPTNET_RATE_LIMIT=100
export CONCEPTNET_RATE_PERIOD=60
```

### Configuration File

Create a `.env` file in your working directory:

```env
# .env file
CONCEPTNET_API_BASE_URL=https://api.conceptnet.io
CONCEPTNET_API_VERSION=5.7
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO
CONCEPTNET_RATE_LIMIT=100
CONCEPTNET_RATE_PERIOD=60
```

## MCP Client Setup

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "conceptnet": {
      "command": "python",
      "args": ["-m", "conceptnet_mcp.server"]
    }
  }
}
```

### Other MCP Clients

For other MCP clients, use the appropriate configuration format with:

- **Command**: `python`
- **Arguments**: `["-m", "conceptnet_mcp.server"]`
- **Working Directory**: Your project directory (optional)

## Running the Server

### Basic Usage

```bash
# Start the server with default settings
python -m conceptnet_mcp.server

# Start with custom host and port
MCP_SERVER_HOST=0.0.0.0 MCP_SERVER_PORT=8080 python -m conceptnet_mcp.server

# Start with debug logging
LOG_LEVEL=DEBUG python -m conceptnet_mcp.server
```

### Docker Compose (Recommended)

The project includes a comprehensive Docker Compose configuration that supports both stdio and HTTP transport modes with production-ready settings.

#### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/infinitnet/conceptnet-mcp.git
cd conceptnet-mcp

# Create logs directory
mkdir -p logs

# Start HTTP transport mode (for web clients)
docker compose --profile http up -d

# Or start stdio transport mode (for desktop clients)
docker compose --profile stdio up -d
```

#### Available Profiles

The Docker Compose configuration includes several profiles for different use cases:

- **`stdio`**: For desktop MCP clients (like Claude Desktop)
- **`http`**: For web clients and remote access
- **`development`**: Development mode with debug logging and auto-reload
- **`production`**: Production-optimized settings with resource limits

#### Configuration Examples

**Development Mode:**
```bash
# Start development server with debug logging
docker compose --profile development up -d conceptnet-mcp-dev

# View logs
docker compose logs -f conceptnet-mcp-dev
```

**Production Mode:**
```bash
# Start production server
docker compose --profile production up -d conceptnet-mcp-prod

# Check health status
docker compose ps
```

**Multiple Transport Modes:**
```bash
# Run both stdio and HTTP modes simultaneously
docker compose --profile stdio --profile http up -d
```

#### Environment Configuration

Create a `.env` file in your project directory to customize settings:

```env
# ConceptNet API Settings
CONCEPTNET_API_BASE_URL=https://api.conceptnet.io
CONCEPTNET_API_VERSION=5.7

# Server Settings
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3001
LOG_LEVEL=INFO

# Rate Limiting
CONCEPTNET_RATE_LIMIT=100
CONCEPTNET_RATE_PERIOD=60
```

#### Service Management

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart services
docker compose restart

# View logs
docker compose logs -f

# Update and rebuild
docker compose pull
docker compose build --no-cache
docker compose up -d

# Clean up
docker compose down -v --remove-orphans
```

#### Health Monitoring

The HTTP transport includes built-in health checks:

```bash
# Check service health
curl http://localhost:3001/health

# Monitor with Docker
docker compose ps
docker compose logs conceptnet-mcp-http
```

#### MCP Client Integration

**For HTTP Transport:**
```json
{
  "mcpServers": {
    "conceptnet": {
      "url": "http://localhost:3001"
    }
  }
}
```

**For Stdio Transport (with Docker):**
```json
{
  "mcpServers": {
    "conceptnet": {
      "command": "docker",
      "args": ["compose", "exec", "conceptnet-mcp-stdio", "python", "-m", "conceptnet_mcp.server"]
    }
  }
}
```

## Troubleshooting

### Common Issues

**Import Error**
```bash
ModuleNotFoundError: No module named 'conceptnet_mcp'
```
Solution: Ensure the package is installed correctly by running `python -c "import conceptnet_mcp"`

**Connection Refused**
```bash
ConnectionRefusedError: [Errno 61] Connection refused
```
Solution: Check if the server is running and the port is correct

**Rate Limiting**
```bash
HTTP 429 Too Many Requests
```
Solution: Adjust `CONCEPTNET_RATE_LIMIT` and `CONCEPTNET_RATE_PERIOD` environment variables

### Debug Mode

Enable debug logging for troubleshooting:

```bash
LOG_LEVEL=DEBUG python -m conceptnet_mcp.server
```

### Health Check

Test server connectivity:

```bash
# Check if server is responding
curl http://localhost:3000/health

# Test MCP protocol
# (Use your MCP client's test functionality)
```

## Cloudflare Workers Deployment

Deploy ConceptNet MCP Server to Cloudflare Workers for global, scalable edge deployment with low-latency access worldwide via Cloudflare's network.

### Overview

The Cloudflare Workers deployment uses a **FastAPI-based architecture** specifically designed for Python Workers, providing:

- **FastAPI Framework**: Manual MCP protocol implementation using FastAPI for HTTP routing
- **Standard Workers Pattern**: Uses `fetch(request, env, ctx)` handler (no Durable Objects)
- **Dual Transport Support**: Both SSE and Streamable HTTP protocol endpoints
- **Serverless Scaling**: Automatic scaling based on demand
- **Workers-Compatible HTTP Client**: Custom `CloudflareHTTPClient` using native `fetch()` instead of httpx
- **Manual MCP Protocol**: JSON-RPC 2.0 MCP messages handled directly without FastMCP framework

### Prerequisites

Before deploying to Cloudflare Workers, ensure you have:

1. **Cloudflare Account**: With Workers plan that supports Python
   - Sign up at [https://dash.cloudflare.com/](https://dash.cloudflare.com/)
   - Workers plan required for Durable Objects (paid plan)

2. **Wrangler CLI**: Cloudflare's deployment tool
   ```bash
   npm install -g wrangler
   ```

3. **Python 3.11+**: For local development and testing
   ```bash
   python --version  # Should be 3.11 or higher
   ```

4. **Domain** (optional): For custom routing and production deployments

### Installation and Setup

#### 1. Install Wrangler CLI

```bash
# Install globally via npm
npm install -g wrangler

# Verify installation
wrangler --version
```

#### 2. Authenticate with Cloudflare

```bash
# Login to your Cloudflare account
wrangler login

# Verify authentication
wrangler whoami
```

#### 3. Navigate to Workers Directory

```bash
cd cloudflare-workers/
```

#### 4. Configure Environment Variables

Copy the environment template and configure your deployment:

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Example `.env` configuration:
```env
# Cloudflare Configuration
CLOUDFLARE_ACCOUNT_ID=your-account-id-here
DOMAIN_NAME=your-domain.com

# ConceptNet API Configuration
CONCEPTNET_API_URL=http://api.conceptnet.io

# MCP Server Configuration
MCP_SERVER_NAME=ConceptNet MCP Server
LOG_LEVEL=INFO

# Performance tuning (optional)
HTTP_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_PER_MINUTE=60
```

#### 5. Configure wrangler.toml

Edit `wrangler.toml` to match your Cloudflare setup:

```toml
name = "conceptnet-mcp-server"
main = "src/main.py"
compatibility_date = "2025-08-20"
compatibility_flags = ["python_workers"]

# Update with your domain for custom routing
# zone_name = "your-domain.com"

# Environment variables
[vars]
CONCEPTNET_API_URL = "http://api.conceptnet.io"
MCP_SERVER_NAME = "ConceptNet MCP Server"
LOG_LEVEL = "INFO"

# Development environment
[env.development.vars]
LOG_LEVEL = "DEBUG"

# Production environment
[env.production.vars]
LOG_LEVEL = "INFO"
```

### Deployment Process

#### Development Deployment

For testing and development:

```bash
# Deploy to development environment
wrangler deploy --env development

# View real-time logs
wrangler tail --env development

# Start local development server
wrangler dev
```

#### Production Deployment

For production deployments:

```bash
# Deploy to production (with confirmation)
wrangler deploy --env production

# Check deployment status
wrangler deployments list

# View production logs
wrangler tail --env production
```

#### Using the Automated Deploy Script

The project includes a comprehensive deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Deploy to development
./deploy.sh development deploy

# Deploy to production with confirmation
./deploy.sh production deploy

# Start development server
./deploy.sh development dev
```

The deploy script provides:
- Prerequisite checking
- Configuration validation
- Automated testing
- Post-deployment verification
- Comprehensive error handling

### Configuration

#### Environment Variables

Configure these variables in `wrangler.toml` under the `[vars]` section:

| Variable | Default | Description |
|----------|---------|-------------|
| `CONCEPTNET_API_URL` | `http://api.conceptnet.io` | ConceptNet API base URL |
| `MCP_SERVER_NAME` | `ConceptNet MCP Server` | Server display name |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARN, ERROR) |
| `HTTP_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed requests |

#### FastAPI Configuration

The deployment uses FastAPI for HTTP routing and MCP protocol handling:

```python
# FastAPI app with CORS support
app = FastAPI(title="ConceptNet MCP Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Standard Workers fetch handler
async def fetch(request, env, ctx):
    # Route requests to appropriate transport endpoints
    # /mcp - Streamable HTTP transport
    # /sse - Server-Sent Events transport
    # /tools - Tools listing
```

#### Custom Domain Setup (Optional)

For production deployments with custom domains:

```toml
# Add routes in wrangler.toml
[[routes]]
pattern = "*/mcp"
zone_name = "your-domain.com"

[[routes]]
pattern = "*/sse"
zone_name = "your-domain.com"
```

### Transport Support

The Cloudflare Workers deployment supports both transport protocols:

#### SSE (Server-Sent Events) Transport

```
https://your-worker.your-subdomain.workers.dev/sse
```

**Example Client Configuration (Direct HTTP):**
```python
import httpx
import json

# Direct HTTP request to SSE endpoint
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://your-worker.your-subdomain.workers.dev/sse/messages",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "concept_lookup",
                "arguments": {"term": "artificial intelligence"}
            }
        }
    )
    result = response.json()
    print(result["result"])
```

#### Streamable HTTP Transport

```
https://your-worker.your-subdomain.workers.dev/mcp
```

**Example Client Configuration (Direct HTTP):**
```python
import httpx
import json

# Direct HTTP request to Streamable HTTP endpoint
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://your-worker.your-subdomain.workers.dev/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "concept_lookup",
                "arguments": {"term": "machine learning"}
            }
        }
    )
    result = response.json()
    print(result["result"])
```

#### MCP Client Integration

**For HTTP Transport:**
```json
{
  "mcpServers": {
    "conceptnet": {
      "url": "https://your-worker.your-subdomain.workers.dev/mcp"
    }
  }
}
```

### Verification

#### Test Deployment Endpoints

```bash
# Test MCP endpoint (should return server info)
curl https://your-worker.your-subdomain.workers.dev/mcp

# Test with a proper MCP tool call
curl -X POST https://your-worker.your-subdomain.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "concept_lookup",
      "arguments": {"term": "test"}
    }
  }'

# Test SSE endpoint
curl https://your-worker.your-subdomain.workers.dev/sse

# Test tools listing
curl https://your-worker.your-subdomain.workers.dev/tools
```

#### Verify Tools Availability

Test each available tool:

```bash
# Test concept_lookup
curl -X POST https://your-worker.your-subdomain.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "concept_lookup",
      "arguments": {"term": "artificial intelligence"}
    }
  }'

# Test concept_query
curl -X POST https://your-worker.your-subdomain.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "concept_query",
      "arguments": {"rel": "IsA", "limit_results": true}
    }
  }'
```

#### Performance Testing

```bash
# Load test with multiple requests
for i in {1..10}; do
  curl -X POST https://your-worker.your-subdomain.workers.dev/mcp \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "id": '$i',
      "method": "tools/call",
      "params": {
        "name": "concept_lookup",
        "arguments": {"term": "test'$i'"}
      }
    }' &
done
wait
```

### Monitoring and Maintenance

#### Real-time Monitoring

```bash
# View real-time logs
wrangler tail --env production

# Filter specific log levels
wrangler tail --env production --format pretty

# Monitor specific requests
wrangler tail --env production --grep "concept_lookup"
```

#### Performance Metrics

Monitor your deployment through:

1. **Cloudflare Dashboard**: Navigate to Workers & Pages > Overview
   - Request volume and error rates
   - CPU time and memory usage
   - Geographic distribution of requests

2. **Wrangler CLI Metrics**:
   ```bash
   # View deployment metrics
   wrangler metrics --env production
   
   # View usage analytics
   wrangler analytics --env production
   ```

3. **Custom Logging**: Implemented in the Durable Object
   - Tool execution times
   - ConceptNet API response times
   - Error frequency and types

#### Maintenance Commands

```bash
# Update deployment
git pull origin main
cd cloudflare-workers/
wrangler deploy --env production

# Rollback to previous deployment
wrangler deployments list
wrangler rollback [deployment-id]

# View deployment history
wrangler deployments list --env production

# Delete worker (if needed)
wrangler delete --env production
```

#### Automated Monitoring Setup

Set up monitoring alerts in Cloudflare Dashboard:
- High error rates (>5%)
- Increased response times (>2s)
- CPU time approaching limits
- Memory usage spikes

### Troubleshooting

#### Common Issues

**1. Import Errors**
```
Error: Module not found
```
**Solution**: Ensure the parent directory path is correct in `main.py`:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
```

**2. Authentication Failures**
```
Error: Authentication failed
```
**Solution**: Re-authenticate with Cloudflare:
```bash
wrangler logout
wrangler login
```

**3. FastAPI Import Errors**
```
Error: FastAPI module not found
```
**Solution**: Verify `requirements.txt` includes FastAPI and dependencies:
```
fastapi>=0.104.0,<1.0.0
pydantic>=2.5.0,<3.0.0
uvicorn[standard]>=0.24.0,<1.0.0
```

**4. Timeout Issues**
```
Error: Request timeout
```
**Solution**: Adjust timeout settings:
- Increase `HTTP_TIMEOUT` in environment variables
- Check ConceptNet API availability
- Monitor CPU time usage in Cloudflare Dashboard

**5. Rate Limiting**
```
HTTP 429 Too Many Requests
```
**Solution**:
- Implement client-side rate limiting
- Contact ConceptNet for API limits
- Consider request batching

**6. Memory Limits**
```
Error: Memory limit exceeded
```
**Solution**:
- Optimize payload sizes
- Implement response streaming
- Use `limit_results: true` for large queries

#### Debug Mode

Enable comprehensive debugging:

```bash
# Deploy with debug logging
wrangler deploy --env development

# Monitor debug logs
wrangler tail --env development --format pretty
```

Add debug configuration in `wrangler.toml`:
```toml
[env.development.vars]
LOG_LEVEL = "DEBUG"
DEBUG_MODE = "true"
VERBOSE_LOGGING = "true"
```

#### Local Testing

Test deployment locally before publishing:

```bash
# Start local development server
cd cloudflare-workers/
wrangler dev

# Test endpoints locally
curl http://localhost:8787/mcp
curl -X POST http://localhost:8787/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "concept_lookup", "parameters": {"term": "test"}}'
```

#### Performance Optimization

**Cost Optimization Recommendations:**

1. **Request Bundling**: Batch multiple ConceptNet requests when possible
2. **Response Caching**: Implement caching for frequently accessed concepts
3. **Rate Limiting**: Implement client-side rate limiting
4. **Payload Optimization**: Use `limit_results` for large responses

**Usage Limits Awareness:**

- **CPU Time**: 30 seconds per request (configurable)
- **Memory**: 128MB per Worker
- **Subrequests**: 50 per request
- **Durable Objects**: Billing per request and duration

#### Support Resources

For deployment-specific issues:

1. **Cloudflare Workers Documentation**: [https://developers.cloudflare.com/workers/](https://developers.cloudflare.com/workers/)
2. **Wrangler CLI Reference**: [https://developers.cloudflare.com/workers/wrangler/](https://developers.cloudflare.com/workers/wrangler/)
3. **Durable Objects Guide**: [https://developers.cloudflare.com/workers/learning/using-durable-objects/](https://developers.cloudflare.com/workers/learning/using-durable-objects/)
4. **Project-Specific Details**: See [`cloudflare-workers/README.md`](../cloudflare-workers/README.md) for additional deployment information

### Security Best Practices

#### Authentication Setup

```bash
# Set API keys using Wrangler secrets
wrangler secret put API_KEY --env production
wrangler secret put JWT_SECRET --env production

# List configured secrets
wrangler secret list --env production
```

#### CORS Configuration

The deployment includes CORS headers for web client compatibility:
```javascript
"Access-Control-Allow-Origin": "*",
"Access-Control-Allow-Methods": "GET, POST, OPTIONS",
"Access-Control-Allow-Headers": "Content-Type, Authorization"
```

For production, consider restricting origins:
```python
# In main.py, update CORS headers
"Access-Control-Allow-Origin": "https://your-frontend.com"
```

#### Rate Limiting Implementation

Implement rate limiting in your FastAPI endpoints:
```python
# Example rate limiting logic in main.py
from fastapi import HTTPException

async def check_rate_limit(request):
    # Implement rate limiting logic here
    if requests_per_minute > 60:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
```

### Next Steps

- Read the [Usage Examples](usage.md) to see the server in action
- Explore the [API Reference](api.md) for detailed technical information
- Check individual [Tool Documentation](tools/) for specific tool usage
- Review [`cloudflare-workers/README.md`](../cloudflare-workers/README.md) for advanced deployment configuration
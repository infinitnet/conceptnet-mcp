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

## Next Steps

- Read the [Usage Examples](usage.md) to see the server in action
- Explore the [API Reference](api.md) for detailed technical information
- Check individual [Tool Documentation](tools/) for specific tool usage
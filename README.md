# ConceptNet MCP Server

A Model Context Protocol (MCP) server that provides seamless access to the ConceptNet knowledge graph through FastMCP framework.

[![CI](https://github.com/infinitnet/conceptnet-mcp/workflows/CI/badge.svg)](https://github.com/infinitnet/conceptnet-mcp/actions/workflows/ci.yml)
[![Release](https://github.com/infinitnet/conceptnet-mcp/workflows/Release/badge.svg)](https://github.com/infinitnet/conceptnet-mcp/actions/workflows/release.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

ConceptNet MCP provides AI assistants and applications with structured access to ConceptNet's semantic knowledge through four powerful MCP tools:

- **Concept Lookup**: Get detailed information about specific concepts
- **Concept Query**: Search and filter concepts with advanced criteria  
- **Related Concepts**: Find concepts connected through semantic relationships
- **Concept Relatedness**: Calculate semantic similarity between concepts

## Features

- 🚀 **FastMCP Integration**: Built on the modern FastMCP framework for optimal performance
- 🔍 **Comprehensive Search**: Advanced querying with language filtering and pagination
- 🌐 **Multi-language Support**: Access ConceptNet's multilingual knowledge base
- 📊 **Semantic Analysis**: Calculate relatedness scores between concepts
- 🔄 **Async Operations**: Full async/await support for non-blocking operations
- 📝 **Type Safety**: Complete Pydantic v2 type validation and IDE support
- 🧪 **Production Ready**: Error handling, logging, and testing
- ⚡ **Optimized Output Formats**: Choose between minimal (~96% smaller) or comprehensive responses

## Output Formats

ConceptNet MCP Server supports two output formats for all tools to optimize performance and reduce token usage:

### Minimal Format (Default - Recommended)
- **Size**: ~96% smaller than verbose format
- **Optimized**: Designed specifically for LLM consumption
- **Content**: Essential data only - concepts, relationships, similarity scores
- **Performance**: Faster processing and reduced API costs
- **Usage**: Perfect for most AI applications and chat interfaces

### Verbose Format (Legacy)
- **Size**: Full ConceptNet response data
- **Content**: Complete metadata, statistics, analysis, and original API responses
- **Usage**: Detailed analysis, debugging, or when full context is needed
- **Backward Compatibility**: Maintains compatibility with existing integrations

### Setting the Format

All tools accept a `verbose` parameter:

```json
{
  "name": "concept_lookup",
  "arguments": {
    "term": "artificial intelligence",
    "verbose": false  // Default: minimal format
  }
}
```

```json
{
  "name": "related_concepts",
  "arguments": {
    "term": "machine learning",
    "verbose": true   // Full detailed format
  }
}
```

**Examples of size difference:**
- Minimal: `{"concept": "dog", "relationships": {"IsA": ["animal", "mammal"]}}`
- Verbose: Full ConceptNet response with complete metadata, statistics, timestamps, etc.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/infinitnet/conceptnet-mcp.git
cd conceptnet-mcp

# Install in development mode
pip install -e .
```

### Running the MCP Server

The server supports both **stdio** (for desktop MCP clients) and **HTTP** (for web clients) transport modes:

#### Stdio Transport (Default - for desktop MCP clients)
```bash
# Start with stdio transport (default)
conceptnet-mcp

# Or explicitly specify stdio
conceptnet-mcp-stdio

# Or use Python module
python -m conceptnet_mcp.server
```

#### HTTP Transport (for web clients)
```bash
# Start HTTP server on localhost:3001
conceptnet-mcp-http

# Or with custom host/port
python -c "from conceptnet_mcp.server import run_http_server; run_http_server('0.0.0.0', 8080)"
```

#### Development Modes
```bash
# Development mode with debug logging
conceptnet-mcp-dev

# Production mode with optimized logging
conceptnet-mcp-prod
```

### MCP Client Integration

#### For Desktop MCP Clients (stdio transport)
Add to your MCP client configuration:

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

#### For Web Applications (HTTP transport)
Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "conceptnet": {
      "command": "python",
      "args": ["-m", "conceptnet_mcp.server", "--transport", "http", "--port", "3001"]
    }
  }
}
```

Or start the HTTP server manually and connect to:
```
http://localhost:3001
```

```javascript
// Example web client connection
const client = new MCPClient('http://localhost:3001');
await client.connect();
```

## ☁️ Cloudflare Workers Deployment

Deploy ConceptNet MCP Server to Cloudflare's global edge network for worldwide access and automatic scaling using a **FastAPI-based implementation** optimized for Python Workers.

[![Deploy to Cloudflare Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/infinitnet/conceptnet-mcp)

### Architecture

The Cloudflare Workers deployment uses a **completely different architecture** from the standard FastMCP server:

- **FastAPI Framework**: Manual MCP protocol implementation using FastAPI for HTTP routing
- **Standard Workers Pattern**: Uses `fetch(request, env, ctx)` handler (no Durable Objects)
- **Native HTTP Client**: Custom `CloudflareHTTPClient` using Workers' native `fetch()` API
- **Manual MCP Protocol**: JSON-RPC 2.0 MCP messages handled directly without FastMCP framework

### Benefits

- 🌍 **Global Edge Network**: Low-latency access worldwide via Cloudflare's CDN
- 🚀 **Auto-scaling**: Serverless scaling based on demand with zero cold starts
- 🔄 **Dual Transport Support**: Both SSE and Streamable HTTP endpoints for maximum compatibility
- 🤖 **Remote MCP Access**: Enable AI agents to access ConceptNet from anywhere
- 💰 **Cost-effective**: Pay only for actual usage with generous free tier

### Quick Deploy

```bash
# Clone and navigate to Workers directory
git clone https://github.com/infinitnet/conceptnet-mcp.git
cd conceptnet-mcp/cloudflare-workers

# Install Wrangler CLI
npm install -g wrangler

# Authenticate and deploy
wrangler login
wrangler deploy
```

### Usage After Deployment

Your ConceptNet MCP Server will be available at:

```
# Streamable HTTP Transport (recommended for MCP clients)
https://your-worker.your-domain.workers.dev/mcp

# SSE Transport (legacy support)
https://your-worker.your-domain.workers.dev/sse

# Tools listing endpoint
https://your-worker.your-domain.workers.dev/tools
```

**Example remote client connection (direct HTTP):**
```python
import httpx
import json

# Connect to your deployed Workers instance
async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://your-worker.your-domain.workers.dev/mcp",
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

For detailed deployment instructions, configuration options, and troubleshooting, see the [Cloudflare Workers Documentation](cloudflare-workers/README.md).

## Available Tools

### 1. Concept Lookup

Get detailed information about a specific concept. Returns all relationships and properties.

```json
{
  "name": "concept_lookup",
  "arguments": {
    "term": "artificial intelligence",
    "language": "en",
    "limit_results": false,
    "target_language": null,
    "verbose": false
  }
}
```

**Parameters:**
- `term` (required): The concept to look up
- `language` (default: "en"): Language code for the concept
- `limit_results` (default: false): Limit to first 20 results for quick queries
- `target_language` (optional): Filter results to specific target language
- `verbose` (default: false): Return detailed format vs minimal format

### 2. Concept Query

Advanced querying with sophisticated multi-parameter filtering.

```json
{
  "name": "concept_query",
  "arguments": {
    "start": "car",
    "rel": "IsA",
    "language": "en",
    "limit_results": false,
    "verbose": false
  }
}
```

**Parameters:**
- `start` (optional): Start concept of relationships
- `end` (optional): End concept of relationships
- `rel` (optional): Relation type (e.g., "IsA", "PartOf")
- `node` (optional): Concept that must be start or end of edges
- `other` (optional): Used with 'node' parameter
- `sources` (optional): Filter by data source
- `language` (default: "en"): Language filter
- `limit_results` (default: false): Limit to 20 results for quick queries
- `verbose` (default: false): Return detailed format vs minimal format

### 3. Related Concepts

Find concepts semantically similar to a given concept using ConceptNet's embeddings.

```json
{
  "name": "related_concepts",
  "arguments": {
    "term": "machine learning",
    "language": "en",
    "filter_language": null,
    "limit": 100,
    "verbose": false
  }
}
```

**Parameters:**
- `term` (required): The concept to find related concepts for
- `language` (default: "en"): Language code for input term
- `filter_language` (optional): Filter results to this language only
- `limit` (default: 100, max: 100): Maximum number of related concepts
- `verbose` (default: false): Return detailed format vs minimal format

### 4. Concept Relatedness

Calculate precise semantic relatedness score between two concepts.

```json
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "artificial intelligence",
    "concept2": "machine learning",
    "language1": "en",
    "language2": "en",
    "verbose": false
  }
}
```

**Parameters:**
- `concept1` (required): First concept for comparison
- `concept2` (required): Second concept for comparison
- `language1` (default: "en"): Language for first concept
- `language2` (default: "en"): Language for second concept
- `verbose` (default: false): Return detailed format vs minimal format

## Configuration

The server can be configured through environment variables:

```bash
# ConceptNet API settings
CONCEPTNET_API_BASE_URL=https://api.conceptnet.io
CONCEPTNET_API_VERSION=5.7

# Server settings
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO

# Rate limiting
CONCEPTNET_RATE_LIMIT=100
CONCEPTNET_RATE_PERIOD=60
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/infinitnet/conceptnet-mcp.git
cd conceptnet-mcp

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## API Reference

### Core Models

- **Concept**: Represents a ConceptNet concept with URI, label, and language
- **Edge**: Represents relationships between concepts with relation types
- **Query**: Structured query parameters for concept searches
- **Response**: Standardized response format with pagination support

### Client Components

- **ConceptNetClient**: Async HTTP client for ConceptNet API
- **PaginationHandler**: Automatic pagination for large result sets
- **ResponseProcessor**: Data processing and normalization

### Utilities

- **Text Processing**: Normalize text (underscores to spaces)
- **Logging**: Structured logging with configurable levels
- **Error Handling**: Comprehensive exception hierarchy

## Architecture

```
conceptnet_mcp/
├── client/           # ConceptNet API client
│   ├── conceptnet_client.py
│   ├── pagination.py
│   └── processor.py
├── models/           # Pydantic data models
│   ├── concept.py
│   ├── edge.py
│   ├── query.py
│   └── response.py
├── tools/            # MCP tool implementations
│   ├── concept_lookup.py
│   ├── concept_query.py
│   ├── related_concepts.py
│   └── concept_relatedness.py
├── utils/            # Utility modules
│   ├── exceptions.py
│   ├── logging.py
│   └── text_utils.py
└── server.py         # FastMCP server entry point
```

## Contributing

1. Fork the repository: https://github.com/infinitnet/conceptnet-mcp
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python run_tests.py`
5. Submit a pull request

### Guidelines

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Include docstrings for public APIs
- Write tests for new functionality
- Update documentation as needed

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [ConceptNet](http://conceptnet.io/) for providing the semantic knowledge base
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io/) specification

## Support

- 📖 **Documentation**: [Read the docs](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/infinitnet/conceptnet-mcp/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/infinitnet/conceptnet-mcp/discussions)
- 🌐 **Author's Website**: [https://infinitnet.io/](https://infinitnet.io/)

---

Built with ❤️ for the AI and semantic web community.
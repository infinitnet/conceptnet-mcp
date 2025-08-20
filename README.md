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

## Available Tools

### 1. Concept Lookup

Get detailed information about a specific concept.

```json
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "dog",
    "language": "en"
  }
}
```

### 2. Concept Query

Search for concepts with advanced filtering.

```json
{
  "name": "concept_query",
  "arguments": {
    "query": "animal",
    "language": "en",
    "limit": 10,
    "offset": 0
  }
}
```

### 3. Related Concepts

Find concepts connected through semantic relationships.

```json
{
  "name": "related_concepts",
  "arguments": {
    "concept": "dog",
    "language": "en",
    "limit": 5
  }
}
```

### 4. Concept Relatedness

Calculate semantic similarity between two concepts.

```json
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "dog",
    "concept2": "cat",
    "language": "en"
  }
}
```

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

### Testing

```bash
# Run all tests
python run_tests.py

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=conceptnet_mcp --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
mypy src/

# Run all quality checks
python validate_production_readiness.py
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
- 📧 **Email**: [Contact Us](mailto:co@infinitnet.io)

---

Built with ❤️ for the AI and semantic web community.
# ConceptNet MCP Server Documentation

Welcome to the ConceptNet MCP Server documentation. This server provides seamless access to the ConceptNet knowledge graph through the Model Context Protocol (MCP).

## Table of Contents

- [Installation Guide](installation.md)
- [Usage Examples](usage.md)
- [API Reference](api.md)
- [Tool Documentation](tools/)
  - [Concept Lookup](tools/concept_lookup.md)
  - [Concept Query](tools/concept_query.md)
  - [Related Concepts](tools/related_concepts.md)
  - [Concept Relatedness](tools/concept_relatedness.md)

## Overview

ConceptNet MCP Server is a production-ready MCP server that bridges AI applications with ConceptNet's vast semantic knowledge base. It provides four powerful tools for semantic analysis and concept exploration.

### Key Features

- **FastMCP Framework**: Built on modern FastMCP for optimal performance
- **Async Operations**: Full async/await support for non-blocking operations
- **Type Safety**: Complete Pydantic v2 validation and IDE support
- **Multi-language**: Support for ConceptNet's multilingual knowledge base
- **Production Ready**: Comprehensive error handling, logging, and testing

### Architecture

The server is organized into modular components:

```
conceptnet_mcp/
├── client/           # ConceptNet API client
├── models/           # Pydantic data models
├── tools/            # MCP tool implementations  
├── utils/            # Utility modules
└── server.py         # FastMCP server entry point
```

## Quick Start

1. **Install**: `git clone https://github.com/infinitnet/conceptnet-mcp.git && cd conceptnet-mcp && pip install -e .`
2. **Run**: `python -m conceptnet_mcp.server`
3. **Connect**: Add to your MCP client configuration

## Tools Overview

| Tool | Purpose | Example Use Case |
|------|---------|------------------|
| [Concept Lookup](tools/concept_lookup.md) | Get detailed concept information | Find all data about "dog" |
| [Concept Query](tools/concept_query.md) | Search and filter concepts | Search for animals |
| [Related Concepts](tools/related_concepts.md) | Find semantic relationships | Find concepts related to "dog" |
| [Concept Relatedness](tools/concept_relatedness.md) | Calculate similarity scores | How similar are "dog" and "cat"? |

## Next Steps

- Read the [Installation Guide](installation.md) for setup instructions
- Explore [Usage Examples](usage.md) for practical implementations
- Check the [API Reference](api.md) for detailed technical information
- Browse individual [Tool Documentation](tools/) for specific tool usage

## Support

- 🐛 [Bug Reports](https://github.com/infinitnet/conceptnet-mcp/issues)
- 💬 [Discussions](https://github.com/infinitnet/conceptnet-mcp/discussions)
- 🌐 [Author's Website](https://infinitnet.io/)
- 📖 [GitHub Repository](https://github.com/infinitnet/conceptnet-mcp)
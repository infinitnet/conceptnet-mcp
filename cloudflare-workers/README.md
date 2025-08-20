# ConceptNet MCP Server - Cloudflare Workers Deployment

This directory contains the Cloudflare Workers deployment of the ConceptNet MCP Server using Python Workers with FastAPI for global, scalable deployment.

## Overview

The Cloudflare Workers deployment provides a Python Workers implementation with:

- **Global Edge Deployment**: Low-latency access worldwide via Cloudflare's network
- **Dual Transport Support**: Both SSE and Streamable HTTP MCP protocol endpoints  
- **Serverless Scaling**: Automatic scaling based on demand
- **Workers-Compatible HTTP Client**: Uses native `fetch()` instead of httpx
- **FastAPI Framework**: Modern, fast HTTP API framework for Python
- **Manual MCP Protocol**: Custom implementation compatible with Workers runtime

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│ Cloudflare Edge  │───▶│ Python Worker   │
│                 │    │   (Global CDN)   │    │ FastAPI App     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐         ┌─────────────────┐
                        │ /sse endpoint│         │   MCP Protocol  │
                        │ /mcp endpoint│         │   Handler       │
                        │ /tools       │         │                 │
                        └──────────────┘         └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  ConceptNet API │
                                                 │ (via fetch())   │
                                                 └─────────────────┘
```

## Files Structure

```
cloudflare-workers/
├── wrangler.toml           # Cloudflare Workers configuration (no Durable Objects)
├── requirements.txt        # Python dependencies
├── src/
│   └── main.py            # Python Workers fetch handler implementation
├── README.md              # This file
├── deploy.sh              # Deployment script
└── .env.example           # Environment variables template
```

## Prerequisites

1. **Cloudflare Account**: With Workers Paid plan for Python support
2. **Wrangler CLI**: Cloudflare's deployment tool (v3.0+)
3. **Python 3.11+**: For local development and testing
4. **Domain** (optional): For custom routing

## Installation

### 1. Install Wrangler CLI

```bash
npm install -g wrangler@latest
```

### 2. Authenticate with Cloudflare

```bash
wrangler login
```

### 3. Configure Environment

Copy the environment template and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Update wrangler.toml

Edit `wrangler.toml` to match your Cloudflare setup:

```toml
name = "conceptnet-mcp-server"
# Uncomment and update routes with your domain
# [[routes]]
# pattern = "*/mcp"  
# zone_name = "your-domain.com"
```

## Deployment

### Development Deployment

```bash
# Deploy to development environment
wrangler deploy --env development

# View logs
wrangler tail
```

### Production Deployment

```bash
# Deploy to production
wrangler deploy --env production

# Check deployment status
wrangler deployments list
```

### Using the Deploy Script

```bash
./deploy.sh
```

## Usage

Once deployed, your ConceptNet MCP Server will be available at:

### Streamable HTTP Transport (Recommended)
```
https://conceptnet-mcp-server.your-subdomain.workers.dev/mcp
```

### SSE Transport (Legacy Support)
```
https://conceptnet-mcp-server.your-subdomain.workers.dev/sse
```

### Tools Listing
```
https://conceptnet-mcp-server.your-subdomain.workers.dev/tools
```

### Example MCP Client Usage

#### Minimal Format (Default)
```json
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "concept_lookup",
    "arguments": {
      "term": "artificial intelligence",
      "language": "en",
      "verbose": false
    }
  }
}
```

#### Verbose Format
```json
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "related_concepts",
    "arguments": {
      "term": "machine learning",
      "language": "en",
      "limit": 100,
      "verbose": true
    }
  }
}
```

### Example with cURL

```bash
# List available tools
curl https://your-worker.workers.dev/tools

# Call a tool with minimal format (default)
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "concept_lookup",
      "arguments": {
        "term": "dog",
        "verbose": false
      }
    }
  }'

# Call a tool with verbose format
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "concept_relatedness",
      "arguments": {
        "concept1": "dog",
        "concept2": "cat",
        "verbose": true
      }
    }
  }'
```

## Configuration

### Environment Variables

Configure these in `wrangler.toml`:

- `CONCEPTNET_API_URL`: ConceptNet API base URL (default: "http://api.conceptnet.io")
- `MCP_SERVER_NAME`: Server display name
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

### Transport Support

The server supports both MCP transports:

1. **Streamable HTTP** (`/mcp`): Modern single-endpoint transport
2. **SSE** (`/sse`): Legacy Server-Sent Events transport

## Available Tools

The server provides four ConceptNet tools with support for two output formats:

1. **`concept_lookup`**: Look up all relationships for a concept
2. **`concept_query`**: Advanced filtered searching with multiple parameters
3. **`related_concepts`**: Find semantically similar concepts (default limit: 100)
4. **`concept_relatedness`**: Calculate precise similarity scores between concepts

## Output Formats

All tools support two output formats for optimal performance and cost efficiency:

### Minimal Format (Default - Recommended)
- **Size**: ~96% smaller than verbose format
- **Optimized**: Designed specifically for LLM consumption and API efficiency
- **Content**: Essential data only - concepts, relationships, similarity scores
- **Performance**: Faster processing, reduced bandwidth, and lower API costs
- **Usage**: Perfect for most AI applications and edge deployments

### Verbose Format (Legacy)
- **Size**: Full ConceptNet response data
- **Content**: Complete metadata, statistics, analysis, and original API responses
- **Usage**: Detailed analysis, debugging, or when full context is needed
- **Backward Compatibility**: Maintains compatibility with existing integrations

### Setting the Format

All tools accept a `verbose` parameter in their arguments:

#### Minimal Format Example (Default)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "concept_lookup",
    "arguments": {
      "term": "artificial intelligence",
      "language": "en",
      "verbose": false
    }
  }
}
```

#### Verbose Format Example
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "related_concepts",
    "arguments": {
      "term": "machine learning",
      "language": "en",
      "limit": 100,
      "verbose": true
    }
  }
}
```

### Tool Parameters

#### concept_lookup
- `term` (required): The concept to look up
- `language` (default: "en"): Language code
- `limit_results` (default: false): Limit to first 20 results
- `target_language` (optional): Filter to specific target language
- `verbose` (default: false): Return detailed format vs minimal format

#### concept_query
- `start` (optional): Start concept of relationships
- `end` (optional): End concept of relationships
- `rel` (optional): Relation type
- `node` (optional): Concept that must be start or end
- `other` (optional): Used with node parameter
- `sources` (optional): Filter by data source
- `language` (default: "en"): Language filter
- `limit_results` (default: false): Limit to first page of results
- `verbose` (default: false): Return detailed format vs minimal format

#### related_concepts
- `term` (required): The concept to find related concepts for
- `language` (default: "en"): Language code
- `filter_language` (optional): Filter results to this language
- `limit` (default: 100, max: 100): Maximum number of results
- `verbose` (default: false): Return detailed format vs minimal format

#### concept_relatedness
- `concept1` (required): First concept for comparison
- `concept2` (required): Second concept for comparison
- `language1` (default: "en"): Language for first concept
- `language2` (default: "en"): Language for second concept
- `verbose` (default: false): Return detailed format vs minimal format

## Monitoring

### View Logs

```bash
# Real-time logs
wrangler tail

# Specific environment
wrangler tail --env production
```

### Performance Metrics

Monitor your deployment via:

1. **Cloudflare Dashboard**: Workers analytics
2. **Wrangler CLI**: `wrangler metrics`
3. **Custom Logging**: Built into the fetch handler

## Troubleshooting

### Common Issues

1. **Import Errors**: Python Workers has limited package support
2. **Timeout Issues**: Adjust timeout settings in `CloudflareHTTPClient`
3. **Rate Limiting**: ConceptNet API rate limits may apply
4. **Dependency Issues**: Only use packages compatible with Workers Python runtime

### Debug Mode

Enable debug logging:

```bash
wrangler deploy --env development
# Debug logs will be more verbose
```

### Local Testing

```bash
# Local development server
wrangler dev

# Test endpoints
curl http://localhost:8787/
curl http://localhost:8787/tools
curl -X POST http://localhost:8787/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Cost Optimization

### Recommendations

1. **Request Bundling**: Batch multiple ConceptNet requests when possible
2. **Response Caching**: Implement caching for frequently accessed concepts
3. **Rate Limiting**: Implement client-side rate limiting
4. **Efficient Endpoints**: Use specific tools rather than broad queries

### Usage Limits

Be aware of Cloudflare Workers limits:

- **CPU Time**: 30 seconds per request (configurable)
- **Memory**: 128MB per Worker
- **Subrequests**: 50 per request
- **Request Size**: 100MB maximum

## Security

### Best Practices

1. **Authentication**: Implement API keys or OAuth if needed
2. **Rate Limiting**: Prevent abuse of the ConceptNet API
3. **CORS**: Configure appropriate CORS headers (implemented)
4. **Secrets**: Use Wrangler secrets for sensitive data

```bash
# Set secrets
wrangler secret put API_KEY
wrangler secret put DATABASE_URL
```

## Development

### Testing Changes

1. Test locally: `wrangler dev`
2. Deploy to development: `wrangler deploy --env development`
3. Monitor logs: `wrangler tail`
4. Deploy to production: `wrangler deploy --env production`

### Code Structure

- **`fetch()` handler**: Main entry point for all requests
- **`MCPProtocol` class**: Handles MCP protocol messages
- **`CloudflareHTTPClient`**: ConceptNet API integration
- **FastAPI app**: HTTP routing and endpoint handling

## Contributing

To contribute to the Workers deployment:

1. Test changes locally with `wrangler dev`
2. Deploy to development environment first
3. Monitor performance and error rates
4. Submit PR with deployment notes

## Support

For issues specific to the Workers deployment:

1. Check Cloudflare Workers Python documentation
2. Review Wrangler CLI logs with `wrangler tail`
3. Test with local development server
4. Open issues with deployment-specific details

## License

Same as the main ConceptNet MCP project: GPL-3.0
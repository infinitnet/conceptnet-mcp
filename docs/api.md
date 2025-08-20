# API Reference

This document provides detailed technical information about the ConceptNet MCP Server API.

## Core Models

### Concept

Represents a ConceptNet concept with URI, label, and language information.

```python
class Concept:
    uri: str          # ConceptNet URI (e.g., "/c/en/dog")
    label: str        # Human-readable label (e.g., "dog")
    language: str     # Language code (e.g., "en", "es", "fr")
```

**Example:**
```json
{
  "uri": "/c/en/artificial_intelligence",
  "label": "artificial intelligence", 
  "language": "en"
}
```

### Edge

Represents relationships between concepts in the ConceptNet graph.

```python
class Edge:
    relation: str     # Relationship type (e.g., "IsA", "RelatedTo")
    start: str        # Source concept URI
    end: str          # Target concept URI
    weight: float     # Relationship strength (0.0-10.0)
    dataset: str      # Data source (optional)
    sources: List[str]  # Source references (optional)
```

**Example:**
```json
{
  "relation": "IsA",
  "start": "/c/en/dog",
  "end": "/c/en/animal",
  "weight": 8.5,
  "dataset": "conceptnet",
  "sources": ["/s/contributor/wikipedia"]
}
```

### Query

Structured parameters for concept searches.

```python
class Query:
    query: str        # Search term
    language: str     # Target language (default: "en")
    limit: int        # Results limit (1-100, default: 20)
    offset: int       # Pagination offset (default: 0)
```

### Response

Standardized response format with pagination support.

```python
class Response:
    data: Union[List, Dict]  # Response data
    total: int              # Total available results
    offset: int             # Current offset
    limit: int              # Applied limit
    has_more: bool          # More results available
```

## Tool Schemas

### 1. concept_lookup

Get detailed information about a specific concept.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "concept": {
      "type": "string",
      "description": "The concept to look up (e.g., 'dog', 'artificial intelligence')"
    },
    "language": {
      "type": "string", 
      "description": "Language code (default: 'en')",
      "default": "en"
    }
  },
  "required": ["concept"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "concept": {"$ref": "#/definitions/Concept"},
    "edges": {
      "type": "array",
      "items": {"$ref": "#/definitions/Edge"}
    },
    "total_edges": {"type": "integer"},
    "languages": {
      "type": "array", 
      "items": {"type": "string"}
    }
  }
}
```

### 2. concept_query

Search and filter concepts with advanced criteria.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search term or phrase"
    },
    "language": {
      "type": "string",
      "description": "Language code (default: 'en')", 
      "default": "en"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum results (1-100, default: 20)",
      "minimum": 1,
      "maximum": 100,
      "default": 20
    },
    "offset": {
      "type": "integer",
      "description": "Pagination offset (default: 0)",
      "minimum": 0,
      "default": 0
    }
  },
  "required": ["query"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "concepts": {
      "type": "array",
      "items": {"$ref": "#/definitions/Concept"}
    },
    "total": {"type": "integer"},
    "offset": {"type": "integer"},
    "limit": {"type": "integer"},
    "has_more": {"type": "boolean"}
  }
}
```

### 3. related_concepts

Find concepts connected through semantic relationships.

**Input Schema:**
```json
{
  "type": "object", 
  "properties": {
    "concept": {
      "type": "string",
      "description": "Source concept"
    },
    "language": {
      "type": "string",
      "description": "Language code (default: 'en')",
      "default": "en"
    },
    "limit": {
      "type": "integer", 
      "description": "Maximum results (1-50, default: 10)",
      "minimum": 1,
      "maximum": 50,
      "default": 10
    }
  },
  "required": ["concept"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "source_concept": {"$ref": "#/definitions/Concept"},
    "related_concepts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "concept": {"$ref": "#/definitions/Concept"},
          "relation": {"type": "string"},
          "weight": {"type": "number"}
        }
      }
    },
    "total": {"type": "integer"}
  }
}
```

### 4. concept_relatedness

Calculate semantic similarity between two concepts.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "concept1": {
      "type": "string",
      "description": "First concept"
    },
    "concept2": {
      "type": "string", 
      "description": "Second concept"
    },
    "language": {
      "type": "string",
      "description": "Language code (default: 'en')",
      "default": "en"
    }
  },
  "required": ["concept1", "concept2"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "concept1": {"$ref": "#/definitions/Concept"},
    "concept2": {"$ref": "#/definitions/Concept"},
    "relatedness_score": {
      "type": "number",
      "description": "Similarity score (0.0-10.0)"
    },
    "explanation": {
      "type": "string",
      "description": "Human-readable explanation"
    },
    "shared_relations": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

## Error Handling

### Standard Error Format

```json
{
  "error": "ErrorType",
  "message": "Human-readable error description",
  "details": {}  // Additional error context
}
```

### Error Types

| Error Type | Description | HTTP Status |
|------------|-------------|-------------|
| `ConceptNotFound` | Concept doesn't exist in ConceptNet | 404 |
| `ValidationError` | Invalid input parameters | 400 |
| `RateLimitExceeded` | Too many requests | 429 |
| `APIError` | ConceptNet API error | 502 |
| `TimeoutError` | Request timeout | 504 |
| `InternalError` | Server internal error | 500 |

### Error Examples

**Concept Not Found:**
```json
{
  "error": "ConceptNotFound",
  "message": "Concept 'invalidconcept' not found in language 'en'",
  "details": {
    "concept": "invalidconcept",
    "language": "en"
  }
}
```

**Validation Error:**
```json
{
  "error": "ValidationError", 
  "message": "Invalid limit value. Must be between 1 and 100.",
  "details": {
    "field": "limit",
    "value": 150,
    "expected": "1-100"
  }
}
```

**Rate Limit Exceeded:**
```json
{
  "error": "RateLimitExceeded",
  "message": "Rate limit exceeded. Please wait before making more requests.",
  "details": {
    "retry_after": 60,
    "limit": 100,
    "period": 60
  }
}
```

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONCEPTNET_API_BASE_URL` | string | `https://api.conceptnet.io` | ConceptNet API base URL |
| `CONCEPTNET_API_VERSION` | string | `5.7` | ConceptNet API version |
| `MCP_SERVER_HOST` | string | `localhost` | Server host |
| `MCP_SERVER_PORT` | integer | `3000` | Server port |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `CONCEPTNET_RATE_LIMIT` | integer | `100` | Requests per period |
| `CONCEPTNET_RATE_PERIOD` | integer | `60` | Rate limit period (seconds) |

### Logging Configuration

The server uses structured logging with configurable levels:

- `DEBUG`: Detailed debugging information
- `INFO`: General information messages  
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

**Example Log Output:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Processing concept lookup",
  "concept": "dog",
  "language": "en",
  "request_id": "req_123456"
}
```

## Rate Limiting

The server implements rate limiting to prevent abuse:

- **Default Limit**: 100 requests per 60 seconds
- **Algorithm**: Token bucket with automatic refill
- **Headers**: Rate limit information in response headers
- **Backoff**: Exponential backoff recommended for retries

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Performance

### Response Times

Typical response times for different operations:

| Operation | Average | 95th Percentile |
|-----------|---------|-----------------|
| concept_lookup | 200ms | 500ms |
| concept_query | 300ms | 800ms |
| related_concepts | 250ms | 600ms |
| concept_relatedness | 400ms | 1000ms |

### Caching

The server implements intelligent caching:

- **Memory Cache**: Frequently accessed concepts
- **TTL**: 1 hour for concept data
- **Invalidation**: Automatic cache refresh

### Pagination

Efficient pagination is implemented for large result sets:

- **Default Page Size**: 20 items
- **Maximum Page Size**: 100 items
- **Cursor-based**: Uses offset for consistent pagination

## Security

### Input Validation

All inputs are validated using Pydantic schemas:

- **Type checking**: Automatic type conversion and validation
- **Range validation**: Numeric ranges and string lengths
- **Sanitization**: Input sanitization to prevent injection

### Error Information

Error responses are carefully crafted to avoid information leakage:

- **No stack traces** in production responses
- **Sanitized error messages** with user-friendly descriptions
- **Request IDs** for error tracking and debugging

## Client Libraries

### Python Client Example

```python
import asyncio
from conceptnet_mcp.client import ConceptNetClient

async def example():
    client = ConceptNetClient()
    
    # Look up a concept
    result = await client.lookup_concept("dog", "en")
    print(f"Found concept: {result.concept.label}")
    
    # Search for concepts
    results = await client.query_concepts("animal", "en", limit=10)
    print(f"Found {results.total} concepts")
    
    await client.close()

asyncio.run(example())
```

### JavaScript/TypeScript Interface

```typescript
interface ConceptLookupParams {
  concept: string;
  language?: string;
}

interface ConceptQueryParams {
  query: string; 
  language?: string;
  limit?: number;
  offset?: number;
}

interface RelatedConceptsParams {
  concept: string;
  language?: string;
  limit?: number;
}

interface ConceptRelatednessParams {
  concept1: string;
  concept2: string;
  language?: string;
}
```

## Next Steps

- Explore [Usage Examples](usage.md) for practical implementations
- Check individual [Tool Documentation](tools/) for detailed tool usage
- Review the [Installation Guide](installation.md) for setup information
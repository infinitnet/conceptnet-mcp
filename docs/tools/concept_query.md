# Concept Query Tool

## Overview

The `concept_query` tool searches for concepts in ConceptNet using flexible search criteria. It provides powerful search capabilities with pagination, language filtering, and relevance scoring to help discover concepts related to your search terms.

## Function Signature

```python
async def concept_query(
    query: str,
    ctx: Context,
    language: str = "en",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | Search term or phrase (e.g., "machine learning", "animal") |
| `ctx` | `Context` | Required | FastMCP context for logging and progress reporting |
| `language` | `str` | `"en"` | Language code for search results (ISO 639-1 format) |
| `limit` | `int` | `20` | Maximum number of results (1-100) |
| `offset` | `int` | `0` | Number of results to skip for pagination |

## Response Structure

### Successful Response

```json
{
  "query_info": {
    "original_query": "animal",
    "normalized_query": "animal",
    "language": "en",
    "search_type": "text_search"
  },
  "concepts": [
    {
      "uri": "/c/en/dog",
      "label": "dog",
      "language": "en",
      "relevance_score": 0.95
    },
    {
      "uri": "/c/en/cat",
      "label": "cat",
      "language": "en",
      "relevance_score": 0.92
    },
    {
      "uri": "/c/en/bird",
      "label": "bird",
      "language": "en",
      "relevance_score": 0.88
    }
  ],
  "pagination": {
    "total": 1500,
    "offset": 0,
    "limit": 20,
    "has_more": true,
    "next_offset": 20
  },
  "metadata": {
    "query_time": "2024-01-20T10:30:00Z",
    "execution_time_ms": 350,
    "endpoint_used": "/search",
    "results_found": 20
  }
}
```

### Error Response

```json
{
  "error": "ValidationError",
  "message": "Query cannot be empty",
  "field": "query",
  "value": "",
  "suggestions": [
    "Provide a meaningful search term",
    "Use keywords related to your domain of interest"
  ]
}
```

## Usage Examples

### Basic Search

```python
result = await concept_query(
    query="animal",
    ctx=context
)
# Returns concepts related to animals
```

### Paginated Search

```python
# First page
page1 = await concept_query(
    query="technology",
    ctx=context,
    limit=50,
    offset=0
)

# Second page
page2 = await concept_query(
    query="technology",
    ctx=context,
    limit=50,
    offset=50
)
```

### Multilingual Search

```python
result = await concept_query(
    query="tecnología",
    ctx=context,
    language="es",
    limit=30
)
# Returns Spanish concepts related to technology
```

### Specific Domain Search

```python
result = await concept_query(
    query="machine learning algorithm",
    ctx=context,
    limit=15
)
# Returns concepts specifically related to ML algorithms
```

### Broad Category Search

```python
result = await concept_query(
    query="emotion",
    ctx=context,
    limit=25
)
# Returns various emotional concepts
```

## Search Features

### Query Processing

The tool automatically processes queries to improve search results:

1. **Text Normalization**: Converts underscores to spaces, handles capitalization
2. **Phrase Handling**: Supports multi-word phrases and compound terms
3. **Fuzzy Matching**: Finds concepts even with minor spelling variations
4. **Synonym Expansion**: May include related terms in search results

### Relevance Scoring

Each result includes a relevance score (0.0-1.0):
- **0.9-1.0**: Exact or very close matches
- **0.7-0.8**: Strong semantic matches
- **0.5-0.6**: Moderate relevance
- **0.3-0.4**: Weak but potentially relevant
- **0.0-0.2**: Low relevance (may be filtered out)

### Search Types

The tool supports different search approaches:

| Search Type | Description | Best For |
|-------------|-------------|----------|
| `text_search` | Direct text matching | Specific terms |
| `semantic_search` | Meaning-based search | Related concepts |
| `prefix_search` | Starting with query | Completion suggestions |
| `fuzzy_search` | Approximate matching | Typo tolerance |

## Pagination

### Basic Pagination

```python
async def search_all_pages(query: str, ctx: Context, page_size: int = 50):
    """Search all pages of results."""
    all_concepts = []
    offset = 0
    
    while True:
        result = await concept_query(
            query=query,
            ctx=ctx,
            limit=page_size,
            offset=offset
        )
        
        all_concepts.extend(result["concepts"])
        
        if not result["pagination"]["has_more"]:
            break
            
        offset = result["pagination"]["next_offset"]
    
    return all_concepts
```

### Efficient Pagination

```python
async def paginated_search(query: str, ctx: Context, max_results: int = 200):
    """Search with result limit."""
    concepts = []
    offset = 0
    page_size = min(50, max_results)
    
    while len(concepts) < max_results:
        remaining = max_results - len(concepts)
        current_limit = min(page_size, remaining)
        
        result = await concept_query(
            query=query,
            ctx=ctx,
            limit=current_limit,
            offset=offset
        )
        
        concepts.extend(result["concepts"])
        
        if not result["pagination"]["has_more"]:
            break
            
        offset += current_limit
    
    return concepts[:max_results]
```

## Advanced Features

### Filtering Results

```python
def filter_by_relevance(concepts: List[Dict], min_score: float = 0.5):
    """Filter concepts by relevance score."""
    return [c for c in concepts if c.get("relevance_score", 0) >= min_score]

def filter_by_pattern(concepts: List[Dict], pattern: str):
    """Filter concepts matching a pattern."""
    import re
    regex = re.compile(pattern, re.IGNORECASE)
    return [c for c in concepts if regex.search(c["label"])]
```

### Sorting Results

```python
def sort_by_relevance(concepts: List[Dict], descending: bool = True):
    """Sort concepts by relevance score."""
    return sorted(
        concepts, 
        key=lambda x: x.get("relevance_score", 0), 
        reverse=descending
    )

def sort_alphabetically(concepts: List[Dict]):
    """Sort concepts alphabetically."""
    return sorted(concepts, key=lambda x: x["label"].lower())
```

### Search Optimization

```python
async def optimized_search(query: str, ctx: Context, target_count: int = 100):
    """Optimized search for specific result count."""
    # Start with reasonable page size
    initial_limit = min(50, target_count)
    
    result = await concept_query(
        query=query,
        ctx=ctx,
        limit=initial_limit
    )
    
    concepts = result["concepts"]
    
    # If we need more and more are available
    if len(concepts) < target_count and result["pagination"]["has_more"]:
        remaining = target_count - len(concepts)
        
        additional = await concept_query(
            query=query,
            ctx=ctx,
            limit=remaining,
            offset=initial_limit
        )
        
        concepts.extend(additional["concepts"])
    
    return concepts[:target_count]
```

## Error Handling

### Common Errors

#### Empty Query

```json
{
  "error": "ValidationError",
  "message": "Query cannot be empty",
  "field": "query",
  "value": ""
}
```

#### Invalid Limit

```json
{
  "error": "ValidationError", 
  "message": "Limit must be between 1 and 100",
  "field": "limit",
  "value": 150
}
```

#### No Results Found

```json
{
  "error": "NoResultsFound",
  "message": "No concepts found for query 'xyz' in language 'en'",
  "query": "xyz",
  "language": "en",
  "suggestions": [
    "Try a more general search term",
    "Check spelling",
    "Try a different language"
  ]
}
```

### Error Recovery

```python
async def robust_search(query: str, ctx: Context, **kwargs):
    """Search with fallback strategies."""
    try:
        return await concept_query(query, ctx, **kwargs)
    except Exception as e:
        if "not found" in str(e).lower():
            # Try more general terms
            words = query.split()
            if len(words) > 1:
                # Try individual words
                for word in words:
                    try:
                        return await concept_query(word, ctx, **kwargs)
                    except:
                        continue
        raise e
```

## Performance Considerations

### Response Times

Typical response times:
- **Simple queries**: 200-400ms
- **Complex phrases**: 300-600ms
- **Large result sets**: 400-800ms
- **Cross-language searches**: May be slightly slower

### Optimization Strategies

1. **Use appropriate page sizes**: 20-50 results per request
2. **Implement caching**: Store frequent search results
3. **Batch related queries**: Group similar searches
4. **Filter early**: Apply filters to reduce data processing

### Rate Limiting

Be aware of ConceptNet's rate limits:
- Default: 100 requests per minute
- Implement backoff strategies for sustained searching
- Consider caching for repeated queries

## Integration Examples

### FastMCP Tool Registration

```python
from fastmcp import FastMCP
from conceptnet_mcp.tools.concept_query import concept_query

mcp = FastMCP("ConceptNet Tools")

# Tool is automatically registered via decorator
# Available as "concept_query" in MCP client
```

### Client Usage

```python
# Via MCP client
result = await client.call_tool("concept_query", {
    "query": "artificial intelligence",
    "language": "en",
    "limit": 30,
    "offset": 0
})

# Access structured data
concepts = result.data["concepts"]
total_available = result.data["pagination"]["total"]
has_more = result.data["pagination"]["has_more"]
```

### Batch Search Processing

```python
import asyncio

async def search_multiple_queries(queries: List[str], ctx: Context):
    """Search multiple queries concurrently."""
    tasks = []
    for query in queries:
        task = concept_query(query, ctx, limit=20)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    processed_results = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results[queries[i]] = {"error": str(result)}
        else:
            processed_results[queries[i]] = result
    
    return processed_results

# Usage
queries = ["animal", "technology", "emotion", "food"]
results = await search_multiple_queries(queries, context)
```

## Best Practices

### Query Design

1. **Use descriptive terms**: More specific queries yield better results
2. **Avoid very common words**: Terms like "thing" or "stuff" may return too many results
3. **Consider compound terms**: Multi-word phrases can be more precise
4. **Use domain-specific language**: Technical terms work well in their domains

### Result Processing

1. **Check relevance scores**: Filter out low-relevance results
2. **Handle empty results**: Always check if concepts array is empty
3. **Implement pagination**: Don't try to load all results at once
4. **Cache frequent searches**: Store results for repeated queries

### Error Handling

1. **Validate inputs**: Check query length and parameters before API calls
2. **Handle timeouts**: Implement appropriate timeout handling
3. **Provide fallbacks**: Have alternative strategies for failed searches
4. **Log for debugging**: Use provided logging for troubleshooting

## Supported Languages

The tool supports all ConceptNet languages:

### High Coverage Languages
- **English (en)**: ~8 million concepts
- **Spanish (es)**: ~2 million concepts  
- **French (fr)**: ~1.5 million concepts
- **German (de)**: ~1 million concepts
- **Chinese (zh)**: ~800k concepts
- **Japanese (ja)**: ~600k concepts

### Other Supported Languages
- **Italian (it)**, **Portuguese (pt)**, **Russian (ru)**, **Dutch (nl)**, 
- **Korean (ko)**, **Arabic (ar)**, and 100+ more languages

### Language-Specific Considerations

```python
# English - highest coverage
result = await concept_query("machine learning", ctx, "en")

# Spanish - good coverage for common terms
result = await concept_query("inteligencia artificial", ctx, "es") 

# Less common languages - may have limited results
result = await concept_query("teknologi", ctx, "id")  # Indonesian
```

## Common Use Cases

### 1. Content Discovery

Find concepts for content creation:

```python
topics = await concept_query("sustainable energy", ctx, limit=50)
# Use results to generate article topics or tags
```

### 2. Semantic Tagging

Generate tags for content classification:

```python
async def generate_tags(content_topic: str, ctx: Context):
    """Generate semantic tags for content."""
    result = await concept_query(content_topic, ctx, limit=20)
    
    # Filter for high-relevance concepts
    tags = [
        concept["label"] 
        for concept in result["concepts"]
        if concept.get("relevance_score", 0) > 0.7
    ]
    
    return tags[:10]  # Return top 10 tags
```

### 3. Search Expansion

Expand user search queries:

```python
async def expand_search_query(original_query: str, ctx: Context):
    """Expand search with related concepts."""
    result = await concept_query(original_query, ctx, limit=10)
    
    related_terms = [concept["label"] for concept in result["concepts"]]
    expanded_query = " OR ".join([original_query] + related_terms[:5])
    
    return expanded_query
```

### 4. Knowledge Exploration

Explore domains of knowledge:

```python
async def explore_domain(domain: str, ctx: Context, depth: int = 3):
    """Explore a knowledge domain."""
    exploration_results = {}
    
    # Start with main domain
    result = await concept_query(domain, ctx, limit=20)
    exploration_results[domain] = result["concepts"]
    
    # Explore related concepts
    for concept in result["concepts"][:depth]:
        concept_name = concept["label"]
        related = await concept_query(concept_name, ctx, limit=10)
        exploration_results[concept_name] = related["concepts"]
    
    return exploration_results
```

## Troubleshooting

### Common Issues

1. **No results**: Query may be too specific or contain typos
2. **Irrelevant results**: Query may be too broad or ambiguous
3. **Slow responses**: Large result sets or network issues
4. **Rate limiting**: Too many requests in short time period

### Debugging Tips

```python
# Enable debug logging
import logging
logging.getLogger("conceptnet_mcp").setLevel(logging.DEBUG)

# Test with simple query first
result = await concept_query("test", ctx, limit=5)

# Check API response details
print(f"Query time: {result['metadata']['execution_time_ms']}ms")
print(f"Results found: {result['metadata']['results_found']}")
```

### Performance Optimization

```python
# Use connection pooling for multiple requests
from aiohttp import ClientSession, TCPConnector

async def optimized_search_session():
    """Create optimized session for multiple searches."""
    connector = TCPConnector(limit=10, limit_per_host=5)
    session = ClientSession(connector=connector)
    
    # Use session for multiple concept_query calls
    # Remember to close session when done
    await session.close()
```

## Next Steps

- Use [Concept Lookup](concept_lookup.md) for detailed concept information
- Explore [Related Concepts](related_concepts.md) for finding concept relationships
- Calculate [Concept Relatedness](concept_relatedness.md) between found concepts
- Review the [API Reference](../api.md) for technical implementation details
# Concept Lookup Tool

## Overview

The `concept_lookup` tool retrieves detailed information about a specific concept from ConceptNet, including its relationships, properties, and associated metadata. This tool provides comprehensive insight into how a concept is represented in the knowledge graph.

## Function Signature

```python
async def concept_lookup(
    concept: str,
    ctx: Context,
    language: str = "en",
    verbose: bool = False
) -> Dict[str, Any]:
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `concept` | `str` | Required | The concept to look up (e.g., "dog", "artificial intelligence") |
| `ctx` | `Context` | Required | FastMCP context for logging and progress reporting |
| `language` | `str` | `"en"` | Language code for the concept (ISO 639-1 format) |
| `verbose` | `bool` | `False` | Output format: `False` for minimal (LLM-optimized), `True` for full ConceptNet format |

## Output Formats

The tool supports two output formats controlled by the `verbose` parameter:

- **`verbose=false` (default)**: Returns minimal format (~96% smaller, LLM-optimized)
- **`verbose=true`**: Returns full ConceptNet response format with complete metadata

### Minimal Format (verbose=false)
```json
{
  "concept": "dog",
  "relationships": [
    {"relation": "IsA", "target": "animal", "weight": 8.5},
    {"relation": "HasProperty", "target": "loyal", "weight": 6.2}
  ],
  "total_relationships": 150
}
```

### Verbose Format (verbose=true)

## Response Structure

### Successful Response

```json
{
  "concept": {
    "uri": "/c/en/dog",
    "label": "dog",
    "language": "en"
  },
  "edges": [
    {
      "relation": "IsA",
      "start": "/c/en/dog",
      "end": "/c/en/animal",
      "weight": 8.5,
      "dataset": "conceptnet",
      "sources": ["/s/contributor/omcs"]
    },
    {
      "relation": "HasProperty",
      "start": "/c/en/dog",
      "end": "/c/en/loyal",
      "weight": 6.2,
      "dataset": "conceptnet"
    }
  ],
  "total_edges": 150,
  "languages": ["en", "es", "fr", "de"],
  "metadata": {
    "query_time": "2024-01-20T10:30:00Z",
    "execution_time_ms": 250,
    "endpoint_used": "/c/en/dog"
  }
}
```

### Error Response

```json
{
  "error": "ConceptNotFound",
  "message": "Concept 'invalidconcept' not found in language 'en'",
  "concept": "invalidconcept",
  "language": "en",
  "suggestions": [
    "Check spelling and try again",
    "Try a more general term",
    "Use a different language"
  ]
}
```

## Usage Examples

### Basic Concept Lookup

```python
result = await concept_lookup(
    concept="dog",
    ctx=context
)
# Returns detailed information about the concept "dog"
```

### Multilingual Lookup

```python
result = await concept_lookup(
    concept="perro",
    ctx=context,
    language="es"
)
# Returns information about "perro" (dog in Spanish)
```

### Abstract Concepts

```python
result = await concept_lookup(
    concept="artificial intelligence",
    ctx=context
)
# Returns information about AI concept and its relationships
```

### Technical Terms

```python
result = await concept_lookup(
    concept="machine learning",
    ctx=context
)
# Returns relationships to programming, AI, algorithms, etc.
```

## Relationship Types

The tool returns various types of relationships that concepts can have:

### Common Relations

| Relation | Description | Example |
|----------|-------------|---------|
| `IsA` | Taxonomic relationship | dog IsA animal |
| `HasProperty` | Attribute relationship | dog HasProperty loyal |
| `UsedFor` | Purpose relationship | car UsedFor transportation |
| `CapableOf` | Ability relationship | bird CapableOf flying |
| `AtLocation` | Location relationship | fish AtLocation water |
| `RelatedTo` | General relationship | dog RelatedTo cat |
| `PartOf` | Component relationship | wheel PartOf car |
| `HasA` | Possession relationship | car HasA engine |

### Relationship Weights

Weights range from 0.0 to 10.0, indicating the strength or confidence of the relationship:
- **8.0-10.0**: Very strong, well-established relationships
- **5.0-7.9**: Strong relationships with good evidence
- **2.0-4.9**: Moderate relationships, may be contextual
- **0.1-1.9**: Weak relationships, limited evidence

## Response Fields

### Concept Object

```json
{
  "uri": "/c/en/dog",      // Unique ConceptNet identifier
  "label": "dog",          // Human-readable label
  "language": "en"         // Language code
}
```

### Edge Object

```json
{
  "relation": "IsA",                        // Relationship type
  "start": "/c/en/dog",                     // Source concept URI
  "end": "/c/en/animal",                    // Target concept URI
  "weight": 8.5,                           // Relationship strength
  "dataset": "conceptnet",                  // Data source
  "sources": ["/s/contributor/omcs"]        // Original sources
}
```

## Error Handling

### Concept Not Found

When a concept doesn't exist in ConceptNet:

```json
{
  "error": "ConceptNotFound",
  "message": "Concept 'xyz' not found in language 'en'",
  "concept": "xyz",
  "language": "en",
  "suggestions": ["Check spelling", "Try synonyms", "Use different language"]
}
```

### Invalid Parameters

For invalid input parameters:

```json
{
  "error": "ValidationError",
  "message": "Concept cannot be empty",
  "field": "concept",
  "value": ""
}
```

### API Errors

For ConceptNet API issues:

```json
{
  "error": "APIError",
  "message": "ConceptNet API temporarily unavailable",
  "status_code": 503,
  "retry_after": 60
}
```

## Advanced Features

### Language Detection

The tool can work with concepts in multiple languages:

```python
# English
await concept_lookup("dog", ctx, "en")

# Spanish  
await concept_lookup("perro", ctx, "es")

# French
await concept_lookup("chien", ctx, "fr")

# German
await concept_lookup("hund", ctx, "de")
```

### Filtering by Relationship Type

While the basic tool returns all relationships, you can filter results:

```python
result = await concept_lookup("dog", ctx)
# Filter for only "IsA" relationships
isa_relations = [edge for edge in result["edges"] if edge["relation"] == "IsA"]
```

### Sorting by Weight

Sort relationships by importance:

```python
result = await concept_lookup("dog", ctx)
# Sort by weight (strongest first)
sorted_edges = sorted(result["edges"], key=lambda x: x["weight"], reverse=True)
```

## Integration Examples

### FastMCP Tool Registration

```python
from fastmcp import FastMCP
from conceptnet_mcp.tools.concept_lookup import concept_lookup

mcp = FastMCP("ConceptNet Tools")

# Tool is automatically registered via decorator
# Available as "concept_lookup" in MCP client
```

### Client Usage

```python
# Via MCP client
result = await client.call_tool("concept_lookup", {
    "concept": "dog",
    "language": "en"
})

# Access structured data
concept_info = result.data["concept"]
relationships = result.data["edges"]
total_relationships = result.data["total_edges"]
```

### Batch Processing

```python
import asyncio

async def lookup_multiple_concepts(concepts, ctx, language="en"):
    tasks = []
    for concept in concepts:
        task = concept_lookup(concept, ctx, language)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
concepts = ["dog", "cat", "bird", "fish"]
results = await lookup_multiple_concepts(concepts, context)
```

## Performance Considerations

### Response Times

Typical response times:
- **Simple concepts**: 100-300ms
- **Complex concepts**: 200-500ms
- **Rare concepts**: 300-800ms
- **Network issues**: May timeout after 30s

### Optimization Tips

1. **Use common terms**: More frequent concepts have faster lookup times
2. **Cache results**: Store frequently accessed concept data locally
3. **Batch requests**: Use asyncio for multiple concurrent lookups
4. **Handle errors gracefully**: Implement retry logic for transient failures

## Best Practices

### Input Validation

```python
def validate_concept(concept: str) -> bool:
    """Validate concept input before lookup."""
    if not concept or not concept.strip():
        return False
    if len(concept) > 200:
        return False
    return True
```

### Error Recovery

```python
async def robust_concept_lookup(concept: str, ctx: Context, language: str = "en"):
    """Concept lookup with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await concept_lookup(concept, ctx, language)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Result Processing

```python
def extract_key_relationships(result: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract key relationship types from lookup result."""
    relationships = {}
    for edge in result.get("edges", []):
        relation = edge["relation"]
        target = edge["end"].split("/")[-1]  # Extract concept name
        
        if relation not in relationships:
            relationships[relation] = []
        relationships[relation].append(target)
    
    return relationships
```

## Supported Languages

The tool supports all languages available in ConceptNet:

- **Major Languages**: English (en), Spanish (es), French (fr), German (de), Chinese (zh), Japanese (ja), Russian (ru)
- **Additional Languages**: Italian (it), Portuguese (pt), Arabic (ar), Dutch (nl), Korean (ko), and many more

### Language Coverage

Language coverage varies significantly:
- **English**: Highest coverage (~8M concepts)
- **Major European Languages**: Good coverage (~1-3M concepts)
- **Other Languages**: Variable coverage (10K-1M concepts)

## Common Use Cases

### 1. Knowledge Graph Exploration

Start with a concept and explore its semantic neighborhood:

```python
result = await concept_lookup("artificial intelligence", ctx)
# Explore relationships to understand AI's conceptual connections
```

### 2. Semantic Search Enhancement

Use concept relationships to expand search queries:

```python
result = await concept_lookup("car", ctx)
# Use related concepts (vehicle, automobile, transportation) for broader search
```

### 3. Content Categorization

Understand how concepts relate to categories:

```python
result = await concept_lookup("novel", ctx)
# Find IsA relationships to determine categories (book, literature, etc.)
```

### 4. Educational Applications

Provide detailed information about learning topics:

```python
result = await concept_lookup("photosynthesis", ctx)
# Get comprehensive relationships for educational content
```

## Troubleshooting

### Common Issues

1. **Concept Not Found**: Try more general terms or check spelling
2. **Empty Results**: Some concepts may have limited relationship data
3. **Slow Responses**: Network latency or ConceptNet load issues
4. **Language Mismatches**: Ensure language code matches concept language

### Debug Information

Enable detailed logging:

```python
import logging
logging.getLogger("conceptnet_mcp").setLevel(logging.DEBUG)

result = await concept_lookup("test", ctx)
# Detailed logs will show API calls and processing steps
```

## Next Steps

- Explore [Related Concepts](related_concepts.md) for finding concept neighbors
- Use [Concept Query](concept_query.md) for searching multiple concepts
- Calculate [Concept Relatedness](concept_relatedness.md) between concept pairs
- Review the [API Reference](../api.md) for technical details
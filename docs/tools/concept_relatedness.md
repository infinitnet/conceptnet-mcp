# Concept Relatedness Tool

## Overview

The `concept_relatedness` tool calculates semantic relatedness scores between two concepts using ConceptNet's embeddings and relatedness algorithms. This tool quantifies how similar or related two concepts are to each other, providing both numeric scores and detailed analysis.

## Key Features

- **Semantic Similarity Calculation**: Uses ConceptNet's embeddings to compute relatedness scores from 0.0 (unrelated) to 1.0 (identical)
- **Cross-Language Support**: Compare concepts across different languages (e.g., "perro" in Spanish vs "dog" in English)
- **Comprehensive Analysis**: Provides descriptive interpretations, relationship insights, and confidence indicators
- **Robust Validation**: Input parameter validation with helpful error messages
- **Performance Optimization**: Efficient API usage with proper error handling and retry logic

## Function Signature

```python
async def concept_relatedness(
    concept1: str,
    concept2: str,
    ctx: Context,
    language1: str = "en",
    language2: str = "en"
) -> Dict[str, Any]:
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `concept1` | `str` | Required | First concept term for comparison (e.g., "dog", "happiness") |
| `concept2` | `str` | Required | Second concept term for comparison (e.g., "cat", "joy") |
| `ctx` | `Context` | Required | FastMCP context for logging and progress reporting |
| `language1` | `str` | `"en"` | Language code for first concept (ISO 639-1 format) |
| `language2` | `str` | `"en"` | Language code for second concept (ISO 639-1 format) |

## Response Structure

### Successful Response

```json
{
  "query_info": {
    "concept1": {
      "term": "dog",
      "normalized": "dog",
      "language": "en",
      "uri": "/c/en/dog"
    },
    "concept2": {
      "term": "cat",
      "normalized": "cat",
      "language": "en",
      "uri": "/c/en/cat"
    },
    "comparison_type": "same_language"
  },
  "relatedness": {
    "score": 0.558,
    "description": "moderate",
    "interpretation": "These concepts are moderately related",
    "percentile": 70,
    "confidence": "medium"
  },
  "analysis": {
    "relationship_strength": "moderate",
    "likely_connections": [
      "Both concepts relate to animals",
      "Concepts may share some common properties",
      "Could be indirectly related through broader categories"
    ],
    "semantic_distance": 0.442,
    "similarity_category": "medium_similarity"
  },
  "metadata": {
    "query_time": "2024-01-20T10:30:00Z",
    "execution_time_ms": 450,
    "endpoint_used": "/relatedness",
    "calculation_method": "conceptnet_embeddings"
  }
}
```

### Error Response

```json
{
  "error": "validation_error",
  "message": "concept1 parameter is required and cannot be empty",
  "field": "concept1",
  "suggestions": ["Provide a meaningful concept term"],
  "concepts": {
    "concept1": "",
    "concept2": "cat",
    "language1": "en",
    "language2": "en"
  },
  "query_time": "2024-01-20T10:30:00Z"
}
```

## Usage Examples

### Basic Same-Language Comparison

```python
result = await concept_relatedness(
    concept1="dog",
    concept2="cat",
    ctx=context
)
# Score: 0.558 (moderate relatedness)
```

### Cross-Language Comparison

```python
result = await concept_relatedness(
    concept1="perro",
    concept2="dog",
    ctx=context,
    language1="es",
    language2="en"
)
# Score: 0.955 (very strong - translation equivalents)
```

### Emotional Concepts

```python
result = await concept_relatedness(
    concept1="happy",
    concept2="joy",
    ctx=context
)
# Score: 0.441 (moderate - related emotions)
```

### Transportation Concepts

```python
result = await concept_relatedness(
    concept1="car",
    concept2="bicycle",
    ctx=context
)
# Score: ~0.3-0.5 (moderate - both transportation)
```

### Unrelated Concepts

```python
result = await concept_relatedness(
    concept1="mathematics",
    concept2="banana",
    ctx=context
)
# Score: 0.017 (very weak - unrelated domains)
```

## Score Interpretation

### Score Ranges

| Score Range | Description | Interpretation |
|-------------|-------------|----------------|
| 0.8 - 1.0 | Very Strong | Synonyms, translations, or very closely related concepts |
| 0.6 - 0.8 | Strong | Related categories, common properties, frequent co-occurrence |
| 0.4 - 0.6 | Moderate | Indirect relationships, shared broader categories |
| 0.2 - 0.4 | Weak | Distant connections, limited shared properties |
| 0.0 - 0.2 | Very Weak | Largely unrelated, different domains |

### Confidence Levels

- **High**: Scores ≥0.7 or ≤0.1 (clear relationship or clear lack thereof)
- **Medium**: Scores 0.3-0.7 (moderate certainty)
- **Low**: Scores 0.1-0.3 (uncertain middle range)

### Percentile Rankings

The tool provides percentile rankings compared to typical concept pairs:
- 95th percentile: Very strong relationships (score ≥0.8)
- 85th percentile: Strong relationships (score ≥0.6)
- 70th percentile: Moderate relationships (score ≥0.4)
- 50th percentile: Weak relationships (score ≥0.2)
- 30th percentile: Very weak relationships (score ≥0.1)
- 15th percentile: Minimal relationships (score <0.1)

## Analysis Features

### Relationship Analysis

The tool provides intelligent analysis including:

1. **Likely Connections**: Explanations for why concepts might be related
2. **Domain Detection**: Automatic detection of common domains (animals, emotions, transportation, etc.)
3. **Textual Similarity**: Recognition of shared word components
4. **Categorical Relationships**: Identification of hierarchical or categorical connections

### Cross-Language Analysis

For cross-language comparisons, the tool provides:
- **Translation Recognition**: High scores for translation equivalents
- **Cultural Differences**: Notes about potential cultural/linguistic variations
- **Confidence Adjustments**: Appropriate confidence levels for cross-language scores

## Error Handling

### Validation Errors

- **Empty Concepts**: Returns clear error for empty or whitespace-only concepts
- **Length Limits**: Enforces 200-character limit for concept terms
- **Language Codes**: Validates language code format and warns about unsupported languages

### API Errors

- **Concept Not Found**: Graceful handling when concepts don't exist in ConceptNet
- **Network Issues**: Retry logic with exponential backoff
- **Service Unavailable**: Clear error messages with suggested actions

### Special Cases

- **Identical Concepts**: Automatic detection and perfect score (1.0) for identical terms
- **Near-Identical**: Recognition of very similar concepts with normalization

## Performance Considerations

### Optimization Features

- **Text Normalization**: Efficient preprocessing to improve cache hits
- **Client Connection Pooling**: Reuses HTTP connections for better performance
- **Timeout Management**: Configurable timeouts to prevent hanging requests
- **Error Recovery**: Graceful degradation when services are unavailable

### Response Times

Typical response times:
- **Cached Results**: 50-100ms
- **Network Requests**: 200-800ms
- **Cross-Language**: May be slightly slower due to additional processing

## Integration Examples

### FastMCP Tool Registration

```python
from fastmcp import FastMCP
from conceptnet_mcp.tools.concept_relatedness import concept_relatedness

mcp = FastMCP("ConceptNet Tools")

# Tool is automatically registered via decorator
# Available as "concept_relatedness" in MCP client
```

### Client Usage

```python
# Via MCP client
result = await client.call_tool("concept_relatedness", {
    "concept1": "dog",
    "concept2": "cat",
    "language1": "en",
    "language2": "en"
})

# Access structured data
score = result.data["relatedness"]["score"]
description = result.data["relatedness"]["description"]
connections = result.data["analysis"]["likely_connections"]
```

### Batch Processing

For processing multiple concept pairs, consider using asyncio:

```python
import asyncio

async def compare_multiple_pairs(pairs, ctx):
    tasks = []
    for concept1, concept2 in pairs:
        task = concept_relatedness(concept1, concept2, ctx)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
pairs = [("dog", "cat"), ("happy", "sad"), ("car", "bicycle")]
results = await compare_multiple_pairs(pairs, context)
```

## Best Practices

### Input Preparation

1. **Use Common Terms**: More common concepts typically have better coverage
2. **Check Spelling**: Typos will result in concept not found errors
3. **Consider Synonyms**: Try alternative terms if initial concepts aren't found
4. **Language Consistency**: Ensure language codes match the actual concept language

### Result Interpretation

1. **Consider Context**: Scores should be interpreted within your specific use case
2. **Use Confidence Levels**: Lower confidence scores may need additional validation
3. **Examine Connections**: The likely_connections provide valuable context
4. **Cross-Language Caution**: Be aware that cross-language scores may vary

### Error Handling

1. **Validate Inputs**: Check concepts before making API calls
2. **Handle Not Found**: Have fallback strategies for missing concepts
3. **Retry Logic**: Implement appropriate retry for network issues
4. **Log for Debugging**: Use the provided logging for troubleshooting

## Supported Languages

The tool supports all languages available in ConceptNet, including:
- **en**: English
- **es**: Spanish
- **fr**: French
- **de**: German
- **it**: Italian
- **pt**: Portuguese
- **ru**: Russian
- **ja**: Japanese
- **zh**: Chinese
- **ar**: Arabic
- And many more...

Note: Language support varies by concept. More common languages and concepts have better coverage.

## Limitations

1. **ConceptNet Coverage**: Limited to concepts available in ConceptNet
2. **Cultural Bias**: May reflect biases present in ConceptNet's data sources
3. **Language Variations**: Some languages have limited concept coverage
4. **Compound Concepts**: Very specific or technical terms may not be well represented
5. **Context Dependency**: Scores represent general relatedness, not context-specific relationships

## Troubleshooting

### Common Issues

1. **"Concept not found"**: Try more general terms or check spelling
2. **Very low scores**: Concepts may be from different domains or poorly represented
3. **Network timeouts**: Check internet connection and ConceptNet API status
4. **Validation errors**: Verify parameter types and values

### Debug Information

The tool provides extensive logging through the FastMCP context:
- **INFO**: High-level operation progress
- **DEBUG**: Detailed processing steps
- **WARNING**: Potential issues that don't prevent execution
- **ERROR**: Critical errors requiring attention

## Future Enhancements

Potential improvements planned:
- **Caching**: Local caching of frequent concept pairs
- **Batch API**: Support for batch relatedness calculations
- **Custom Algorithms**: Alternative similarity calculation methods
- **Confidence Scoring**: More sophisticated confidence calculations
- **Domain Filtering**: Filter results by specific domains or categories
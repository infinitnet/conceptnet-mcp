# Usage Examples

This guide provides practical examples of using the ConceptNet MCP Server tools.

## Overview

The ConceptNet MCP Server provides four main tools for semantic analysis:

1. **concept_lookup** - Get detailed information about a specific concept
2. **concept_query** - Search and filter concepts with advanced criteria
3. **related_concepts** - Find concepts connected through semantic relationships
4. **concept_relatedness** - Calculate semantic similarity between concepts

## Tool Examples

### 1. Concept Lookup

Get detailed information about a specific concept.

**Basic Example:**
```json
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "dog",
    "language": "en"
  }
}
```

**Response:**
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
      "weight": 8.5
    },
    {
      "relation": "HasProperty",
      "start": "/c/en/dog",
      "end": "/c/en/loyal",
      "weight": 6.2
    }
  ],
  "total_edges": 150,
  "languages": ["en", "es", "fr", "de"]
}
```

**Multilingual Example:**
```json
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "perro",
    "language": "es"
  }
}
```

### 2. Concept Query

Search for concepts with advanced filtering options.

**Basic Search:**
```json
{
  "name": "concept_query",
  "arguments": {
    "query": "animal",
    "language": "en",
    "limit": 10
  }
}
```

**Response:**
```json
{
  "concepts": [
    {
      "uri": "/c/en/dog",
      "label": "dog",
      "language": "en"
    },
    {
      "uri": "/c/en/cat",
      "label": "cat", 
      "language": "en"
    },
    {
      "uri": "/c/en/bird",
      "label": "bird",
      "language": "en"
    }
  ],
  "total": 1500,
  "offset": 0,
  "limit": 10,
  "has_more": true
}
```

**Advanced Search with Pagination:**
```json
{
  "name": "concept_query",
  "arguments": {
    "query": "machine learning",
    "language": "en",
    "limit": 20,
    "offset": 40
  }
}
```

**Multilingual Search:**
```json
{
  "name": "concept_query",
  "arguments": {
    "query": "tecnología",
    "language": "es",
    "limit": 15
  }
}
```

### 3. Related Concepts

Find concepts connected through semantic relationships.

**Basic Example:**
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

**Response:**
```json
{
  "source_concept": {
    "uri": "/c/en/dog",
    "label": "dog",
    "language": "en"
  },
  "related_concepts": [
    {
      "concept": {
        "uri": "/c/en/cat",
        "label": "cat",
        "language": "en"
      },
      "relation": "SimilarTo",
      "weight": 7.8
    },
    {
      "concept": {
        "uri": "/c/en/animal",
        "label": "animal", 
        "language": "en"
      },
      "relation": "IsA",
      "weight": 8.5
    },
    {
      "concept": {
        "uri": "/c/en/pet",
        "label": "pet",
        "language": "en"
      },
      "relation": "IsA",
      "weight": 7.2
    }
  ],
  "total": 150
}
```

**Technology Domain Example:**
```json
{
  "name": "related_concepts", 
  "arguments": {
    "concept": "artificial intelligence",
    "language": "en",
    "limit": 8
  }
}
```

### 4. Concept Relatedness

Calculate semantic similarity between two concepts.

**Basic Example:**
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

**Response:**
```json
{
  "concept1": {
    "uri": "/c/en/dog",
    "label": "dog",
    "language": "en"
  },
  "concept2": {
    "uri": "/c/en/cat", 
    "label": "cat",
    "language": "en"
  },
  "relatedness_score": 7.8,
  "explanation": "Both are domestic animals and pets",
  "shared_relations": [
    "IsA animal",
    "IsA pet",
    "HasProperty domestic"
  ]
}
```

**Comparing Abstract Concepts:**
```json
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "love",
    "concept2": "happiness",
    "language": "en"
  }
}
```

**Cross-Domain Comparison:**
```json
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "computer",
    "concept2": "brain",
    "language": "en"
  }
}
```

## Common Use Cases

### 1. Semantic Search Enhancement

Use concept query and related concepts to enhance search results:

```json
// First, search for concepts
{
  "name": "concept_query",
  "arguments": {
    "query": "renewable energy",
    "language": "en",
    "limit": 5
  }
}

// Then find related concepts for each result
{
  "name": "related_concepts",
  "arguments": {
    "concept": "solar power", 
    "language": "en",
    "limit": 10
  }
}
```

### 2. Content Recommendation

Calculate relatedness to recommend similar content:

```json
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "machine learning",
    "concept2": "data science",
    "language": "en"
  }
}
```

### 3. Knowledge Graph Exploration

Start with a concept and explore its neighborhood:

```json
// 1. Get detailed information
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "neural network",
    "language": "en"
  }
}

// 2. Find related concepts
{
  "name": "related_concepts",
  "arguments": {
    "concept": "neural network",
    "language": "en",
    "limit": 10
  }
}

// 3. Explore relationships
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "neural network",
    "concept2": "deep learning",
    "language": "en"
  }
}
```

### 4. Multilingual Analysis

Work with concepts across languages:

```json
// English concept
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "artificial intelligence",
    "language": "en"
  }
}

// Spanish equivalent
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "inteligencia artificial",
    "language": "es"
  }
}

// Compare across languages
{
  "name": "concept_relatedness",
  "arguments": {
    "concept1": "machine learning",
    "concept2": "aprendizaje automático",
    "language": "en"
  }
}
```

## Error Handling

The server provides comprehensive error responses:

**Concept Not Found:**
```json
{
  "error": "ConceptNotFound",
  "message": "Concept 'invalidconcept' not found in language 'en'",
  "concept": "invalidconcept",
  "language": "en"
}
```

**Rate Limiting:**
```json
{
  "error": "RateLimitExceeded", 
  "message": "Rate limit exceeded. Please wait before making more requests.",
  "retry_after": 60
}
```

**Invalid Parameters:**
```json
{
  "error": "ValidationError",
  "message": "Invalid limit value. Must be between 1 and 100.",
  "field": "limit",
  "value": 150
}
```

## Best Practices

### 1. Efficient Pagination

Use pagination for large result sets:

```json
{
  "name": "concept_query",
  "arguments": {
    "query": "science",
    "language": "en", 
    "limit": 50,
    "offset": 0
  }
}
```

### 2. Language Consistency

Keep language consistent across related queries:

```json
// All queries use the same language
{
  "name": "concept_lookup",
  "arguments": {
    "concept": "technology",
    "language": "en"
  }
}

{
  "name": "related_concepts",
  "arguments": {
    "concept": "technology",
    "language": "en",
    "limit": 10
  }
}
```

### 3. Rate Limit Awareness

Implement appropriate delays between requests to respect rate limits.

### 4. Error Recovery

Implement retry logic with exponential backoff for transient errors.

## Next Steps

- Explore the [API Reference](api.md) for detailed parameter information
- Check individual [Tool Documentation](tools/) for advanced usage
- Review the [Installation Guide](installation.md) for configuration options
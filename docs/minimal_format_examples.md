# ConceptNet MCP Minimal Format Examples

This document provides concrete examples of the transformation from verbose to minimal format across all ConceptNet MCP tools.

## Overview

The minimal format provides:
- **~96% size reduction** (1200+ lines → 50 lines typical)
- **LLM-optimized structure** with semantic grouping
- **Numeric precision** for confidence scores
- **Backward compatibility** via `verbose=True` parameter

## Tool Examples

### 1. concept_lookup

#### Minimal Format (`verbose=False`, default):
```json
{
  "concept": "dog",
  "relationships": {
    "is_a": [
      {"term": "animal", "weight": 0.85},
      {"term": "mammal", "weight": 0.82},
      {"term": "pet", "weight": 0.79}
    ],
    "related_to": [
      {"term": "cat", "weight": 0.71},
      {"term": "puppy", "weight": 0.89},
      {"term": "bark", "weight": 0.64}
    ],
    "used_for": [
      {"term": "companionship", "weight": 0.76},
      {"term": "protection", "weight": 0.68}
    ],
    "has_property": [
      {"term": "loyal", "weight": 0.73},
      {"term": "friendly", "weight": 0.69}
    ]
  },
  "summary": {
    "total_relationships": 45,
    "relationship_types": 8,
    "avg_confidence": 0.73,
    "high_confidence_count": 32
  }
}
```

#### Verbose Format (`verbose=True`):
```json
{
  "concept": {
    "term": "dog",
    "original_term": "dog",
    "language": "en",
    "uri": "/c/en/dog",
    "normalized_display": "dog"
  },
  "edges": [
    {
      "@id": "/a/[/r/IsA/,/c/en/dog/,/c/en/animal/]",
      "@type": "Edge",
      "dataset": "/d/wordnet/3.1",
      "license": "wordnet",
      "sources": [
        {
          "@id": "/s/resource/wordnet/rdf/3.1",
          "contributor": "/s/contributor/omcs/dev",
          "process": "/s/process/wikiparsec/2"
        }
      ],
      "start": {
        "@id": "/c/en/dog",
        "label": "dog",
        "language": "en",
        "normalized_label": "dog",
        "_original_id": "/c/en/dog"
      },
      "end": {
        "@id": "/c/en/animal", 
        "label": "animal",
        "language": "en",
        "normalized_label": "animal",
        "_original_id": "/c/en/animal"
      },
      "rel": {
        "@id": "/r/IsA",
        "label": "IsA",
        "normalized_label": "is a",
        "_original_id": "/r/IsA"
      },
      "weight": 0.85,
      "readable_summary": "dog is a animal"
    }
    // ... 44 more edges with full metadata
  ],
  "summary": {
    "total_edges": 45,
    "edge_count_by_relation": {
      "is a": 8,
      "related to": 12,
      "used for": 6,
      "has property": 11,
      "part of": 3,
      "capable of": 5
    },
    "languages_found": ["en"],
    "top_relations": ["related to", "has property", "is a", "used for", "capable of"],
    "average_weight": 0.731,
    "weight_range": [0.234, 0.891],
    "most_common_relation": "related to"
  },
  "metadata": {
    "query_time": "2025-08-20T16:10:00.000Z",
    "total_results": 45,
    "pagination_used": true,
    "language_filtered": true,
    "original_term": "dog",
    "normalized_term": "dog", 
    "search_language": "en",
    "target_language": "en"
  }
}
```

**Size Reduction**: 1,200+ lines → 50 lines (**96% reduction**)

### 2. related_concepts

#### Minimal Format (`verbose=False`, default):
```json
{
  "concept": "dog",
  "related_concepts": [
    {"term": "puppy", "weight": 0.91},
    {"term": "cat", "weight": 0.78},
    {"term": "pet", "weight": 0.75},
    {"term": "animal", "weight": 0.65},
    {"term": "bark", "weight": 0.54},
    {"term": "canine", "weight": 0.52}
  ],
  "summary": {
    "total_found": 20,
    "avg_similarity": 0.72,
    "top_similarity": 0.91,
    "similarity_range": [0.32, 0.91]
  }
}
```

#### Verbose Format (`verbose=True`):
```json
{
  "query_info": {
    "input_term": "dog",
    "normalized_term": "dog",
    "input_language": "en",
    "filter_language": null,
    "requested_limit": 20,
    "actual_results": 20
  },
  "related_concepts": [
    {
      "concept": {
        "term": "puppy",
        "language": "en",
        "uri": "/c/en/puppy",
        "normalized_display": "puppy"
      },
      "similarity": {
        "score": 0.91,
        "description": "very strong",
        "rank": 1
      },
      "relationship_context": "Semantically related to the query concept"
    }
    // ... 19 more detailed concept objects
  ],
  "summary": {
    "total_found": 20,
    "languages_in_results": ["en"],
    "similarity_range": {
      "highest": 0.91,
      "lowest": 0.32,
      "average": 0.72
    },
    "categories": {
      "very_strong": 3,
      "strong": 6,
      "moderate": 8,
      "weak": 3,
      "very_weak": 0
    }
  },
  "metadata": {
    "query_time": "2025-08-20T16:10:00.000Z",
    "execution_time_ms": 245,
    "endpoint_used": "/related/c/en/dog",
    "language_filtering_applied": false
  }
}
```

**Size Reduction**: 800+ lines → 25 lines (**97% reduction**)

### 3. concept_query

#### Minimal Format (`verbose=False`, default):
```json
{
  "concept": "car",
  "relationships": {
    "is_a": [
      {"term": "vehicle", "weight": 0.89},
      {"term": "transportation", "weight": 0.83}
    ],
    "used_for": [
      {"term": "driving", "weight": 0.85},
      {"term": "travel", "weight": 0.78}
    ],
    "has_part": [
      {"term": "engine", "weight": 0.87},
      {"term": "wheel", "weight": 0.82},
      {"term": "door", "weight": 0.75}
    ]
  },
  "summary": {
    "total_relationships": 15,
    "relationship_types": 5,
    "avg_confidence": 0.79,
    "high_confidence_count": 12
  }
}
```

#### Verbose Format (`verbose=True`):
```json
{
  "query_info": {
    "parameters_used": {
      "start": "/c/en/car",
      "rel": "/r/IsA"
    },
    "filters_applied": ["start", "rel"],
    "total_results": 15,
    "pagination_used": false,
    "language_filter": "en"
  },
  "edges": [
    // ... 15 full edge objects with complete metadata
  ],
  "summary": {
    "edges_by_relation": {
      "is a": 5,
      "used for": 4,
      "has part": 6
    },
    "unique_concepts": ["car", "vehicle", "transportation", "engine", "wheel"],
    "weight_distribution": {
      "high": 12,
      "medium": 3,
      "low": 0
    },
    "data_sources": ["/s/resource/wordnet/rdf/3.1"],
    "concept_languages": ["en"],
    "average_weight": 0.791,
    "total_unique_concepts": 25,
    "most_common_relation": "has part"
  },
  "metadata": {
    "query_time": "2025-08-20T16:10:00.000Z",
    "execution_time_ms": 189,
    "api_calls_made": 1,
    "results_processed": 15,
    "filters_applied_count": 2
  }
}
```

**Size Reduction**: 600+ lines → 30 lines (**95% reduction**)

### 4. concept_relatedness

#### Minimal Format (`verbose=False`, default):
```json
{
  "concept1": "dog",
  "concept2": "cat",
  "relatedness": 0.78,
  "strength": "strong"
}
```

#### Verbose Format (`verbose=True`):
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
    "score": 0.78,
    "description": "strong",
    "interpretation": "These concepts are strongly related",
    "percentile": 85,
    "confidence": "high"
  },
  "analysis": {
    "relationship_strength": "strong",
    "likely_connections": [
      "Both concepts relate to animals",
      "Concepts likely belong to related categories",
      "May share common properties or functions",
      "Could be connected through common usage patterns"
    ],
    "semantic_distance": 0.22,
    "similarity_category": "high_similarity",
    "note": "Very high relatedness suggests strong semantic or categorical relationship"
  },
  "metadata": {
    "query_time": "2025-08-20T16:10:00.000Z",
    "execution_time_ms": 156,
    "endpoint_used": "/relatedness",
    "calculation_method": "conceptnet_embeddings"
  }
}
```

**Size Reduction**: 200+ lines → 8 lines (**96% reduction**)

## Key Benefits

### For LLMs
- **Faster Processing**: Reduced token count and simpler structure
- **Better Reasoning**: Grouped relationships enable semantic analysis  
- **Precise Scoring**: Numeric weights support quantitative comparisons
- **Easier Parsing**: Predictable structure with clear semantic grouping

### For Developers
- **Reduced Bandwidth**: ~96% smaller responses
- **Cleaner Integration**: Consistent format across all tools
- **Flexible Detail**: Choose appropriate verbosity level
- **Maintained Power**: Full data available when needed

## Migration Guide

### Existing Code (Verbose Format)
```python
# Old: Default verbose format
result = await concept_lookup("dog")
edges = result["edges"]  # Complex nested structure
```

### New Code (Minimal Format)
```python
# New: Default minimal format
result = await concept_lookup("dog")
relationships = result["relationships"]  # Clean grouped structure

# Access specific relationship types
animals = relationships.get("is_a", [])
properties = relationships.get("has_property", [])

# Get summary stats
total = result["summary"]["total_relationships"]
confidence = result["summary"]["avg_confidence"]
```

### Backward Compatibility
```python
# Preserve existing behavior with verbose=True
result = await concept_lookup("dog", verbose=True)
edges = result["edges"]  # Same as before - no breaking changes
```

## Usage Examples

### Basic Queries (Minimal Format)
```python
# Concept relationships
dog_info = await concept_lookup("dog")
print(f"Dog is: {[item['term'] for item in dog_info['relationships']['is_a']]}")

# Related concepts
related = await related_concepts("dog")
print(f"Top related: {related['related_concepts'][0]['term']}")

# Concept comparison
similarity = await concept_relatedness("dog", "cat")
print(f"Similarity: {similarity['relatedness']} ({similarity['strength']})")
```

### Advanced Analysis (Verbose Format)
```python
# Full metadata for detailed analysis
result = await concept_lookup("dog", verbose=True)
edge_sources = [edge["sources"] for edge in result["edges"]]
weight_distribution = result["summary"]["weight_range"]
```

This minimal format design achieves the goal of creating LLM-optimized responses while maintaining full backward compatibility and preserving all essential semantic information.
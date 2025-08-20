# Related Concepts Tool

## Overview

The `related_concepts` tool finds concepts that are semantically connected to a source concept through various relationship types in ConceptNet. This tool is perfect for discovering concept neighborhoods, exploring semantic associations, and understanding how concepts relate to each other.

## Function Signature

```python
async def related_concepts(
    concept: str,
    ctx: Context,
    language: str = "en",
    limit: int = 100,
    verbose: bool = False
) -> Dict[str, Any]:
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `concept` | `str` | Required | Source concept to find relationships for (e.g., "dog", "happiness") |
| `ctx` | `Context` | Required | FastMCP context for logging and progress reporting |
| `language` | `str` | `"en"` | Language code for the concept (ISO 639-1 format) |
| `limit` | `int` | `100` | Maximum number of related concepts to return (1-100) |
| `verbose` | `bool` | `False` | Output format: `False` for minimal (LLM-optimized), `True` for full ConceptNet format |

## Output Formats

The tool supports two output formats controlled by the `verbose` parameter:

- **`verbose=false` (default)**: Returns minimal format (~96% smaller, LLM-optimized)
- **`verbose=true`**: Returns full ConceptNet response format with complete metadata

### Minimal Format (verbose=false)
```json
{
  "concept": "dog",
  "related": [
    {"concept": "cat", "relation": "SimilarTo", "weight": 7.8},
    {"concept": "animal", "relation": "IsA", "weight": 8.5},
    {"concept": "pet", "relation": "IsA", "weight": 6.9}
  ],
  "total_found": 150
}
```

### Verbose Format (verbose=true)

## Response Structure

### Successful Response

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
      "weight": 7.8,
      "direction": "bidirectional"
    },
    {
      "concept": {
        "uri": "/c/en/animal",
        "label": "animal",
        "language": "en"
      },
      "relation": "IsA",
      "weight": 8.5,
      "direction": "outgoing"
    },
    {
      "concept": {
        "uri": "/c/en/puppy",
        "label": "puppy",
        "language": "en"
      },
      "relation": "IsA",
      "weight": 6.2,
      "direction": "incoming"
    }
  ],
  "relationship_summary": {
    "total_found": 150,
    "returned": 10,
    "by_relation": {
      "IsA": 3,
      "SimilarTo": 2,
      "HasProperty": 2,
      "RelatedTo": 3
    },
    "by_direction": {
      "outgoing": 6,
      "incoming": 2,
      "bidirectional": 2
    }
  },
  "metadata": {
    "query_time": "2024-01-20T10:30:00Z",
    "execution_time_ms": 320,
    "endpoint_used": "/c/en/dog",
    "relationship_coverage": "high"
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

### Basic Related Concepts

```python
result = await related_concepts(
    concept="dog",
    ctx=context
)
# Returns concepts related to "dog" (cat, animal, pet, etc.)
```

### Technology Domain

```python
result = await related_concepts(
    concept="artificial intelligence",
    ctx=context,
    limit=15
)
# Returns AI-related concepts (machine learning, neural networks, etc.)
```

### Multilingual Relationships

```python
result = await related_concepts(
    concept="amor",
    ctx=context,
    language="es",
    limit=8
)
# Returns Spanish concepts related to "love"
```

### Abstract Concepts

```python
result = await related_concepts(
    concept="happiness",
    ctx=context,
    limit=12
)
# Returns emotion-related concepts (joy, contentment, smile, etc.)
```

### Scientific Terms

```python
result = await related_concepts(
    concept="photosynthesis",
    ctx=context,
    limit=20
)
# Returns biology-related concepts (plant, chlorophyll, sunlight, etc.)
```

## Relationship Types

The tool returns various types of semantic relationships:

### Core Relationships

| Relation | Description | Example | Direction |
|----------|-------------|---------|-----------|
| `IsA` | Taxonomic relationship | dog IsA animal | Outgoing |
| `HasProperty` | Attribute relationship | dog HasProperty loyal | Outgoing |
| `PartOf` | Component relationship | wheel PartOf car | Outgoing |
| `UsedFor` | Purpose relationship | car UsedFor transportation | Outgoing |
| `CapableOf` | Ability relationship | bird CapableOf flying | Outgoing |
| `AtLocation` | Spatial relationship | fish AtLocation water | Outgoing |
| `RelatedTo` | General association | dog RelatedTo cat | Bidirectional |
| `SimilarTo` | Similarity relationship | dog SimilarTo wolf | Bidirectional |

### Relationship Directions

- **Outgoing**: Source concept → Target concept (dog → animal)
- **Incoming**: Target concept → Source concept (puppy → dog)  
- **Bidirectional**: Mutual relationship (dog ↔ cat)

### Relationship Weights

Weights indicate relationship strength (0.0-10.0):
- **8.0-10.0**: Very strong, well-established relationships
- **6.0-7.9**: Strong relationships with good evidence
- **4.0-5.9**: Moderate relationships, contextually relevant
- **2.0-3.9**: Weak relationships, may be peripheral
- **0.1-1.9**: Very weak relationships, limited evidence

## Advanced Features

### Filtering by Relationship Type

```python
def filter_by_relation(result: Dict[str, Any], relation_type: str) -> List[Dict]:
    """Filter results by specific relationship type."""
    return [
        item for item in result["related_concepts"]
        if item["relation"] == relation_type
    ]

# Usage
result = await related_concepts("dog", ctx, limit=20)
isa_relations = filter_by_relation(result, "IsA")
```

### Sorting by Weight

```python
def sort_by_weight(result: Dict[str, Any], descending: bool = True) -> List[Dict]:
    """Sort related concepts by relationship weight."""
    return sorted(
        result["related_concepts"],
        key=lambda x: x["weight"],
        reverse=descending
    )

# Usage
result = await related_concepts("dog", ctx, limit=15)
strongest_relations = sort_by_weight(result)[:5]
```

### Grouping by Direction

```python
def group_by_direction(result: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """Group related concepts by relationship direction."""
    groups = {"outgoing": [], "incoming": [], "bidirectional": []}
    
    for item in result["related_concepts"]:
        direction = item["direction"]
        groups[direction].append(item)
    
    return groups

# Usage
result = await related_concepts("dog", ctx, limit=20)
grouped = group_by_direction(result)
```

### Multi-hop Exploration

```python
async def explore_concept_neighborhood(
    concept: str, 
    ctx: Context, 
    depth: int = 2,
    max_per_level: int = 5
) -> Dict[str, Any]:
    """Explore multiple levels of concept relationships."""
    
    exploration = {"levels": {}, "all_concepts": set()}
    exploration["levels"][0] = [{"concept": concept, "path": [concept]}]
    exploration["all_concepts"].add(concept)
    
    for level in range(depth):
        exploration["levels"][level + 1] = []
        
        for item in exploration["levels"][level]:
            current_concept = item["concept"]
            
            try:
                result = await related_concepts(
                    current_concept, 
                    ctx, 
                    limit=max_per_level
                )
                
                for related in result["related_concepts"]:
                    related_concept = related["concept"]["label"]
                    
                    if related_concept not in exploration["all_concepts"]:
                        exploration["all_concepts"].add(related_concept)
                        exploration["levels"][level + 1].append({
                            "concept": related_concept,
                            "relation": related["relation"],
                            "weight": related["weight"],
                            "path": item["path"] + [related_concept]
                        })
                        
            except Exception as e:
                # Log error but continue exploration
                print(f"Error exploring {current_concept}: {e}")
    
    return exploration

# Usage
neighborhood = await explore_concept_neighborhood("dog", context, depth=2)
```

## Performance Optimization

### Batch Processing

```python
import asyncio

async def get_related_for_multiple(
    concepts: List[str], 
    ctx: Context,
    limit: int = 10,
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """Get related concepts for multiple source concepts."""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_concept(concept: str):
        async with semaphore:
            try:
                return await related_concepts(concept, ctx, limit=limit)
            except Exception as e:
                return {"error": str(e), "concept": concept}
    
    tasks = [process_concept(concept) for concept in concepts]
    results = await asyncio.gather(*tasks)
    
    return dict(zip(concepts, results))

# Usage
concepts = ["dog", "cat", "bird", "fish"]
all_results = await get_related_for_multiple(concepts, context)
```

### Caching Strategy

```python
from functools import lru_cache
import json

class RelatedConceptsCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def _make_key(self, concept: str, language: str, limit: int) -> str:
        return f"{concept}:{language}:{limit}"
    
    async def get_related(self, concept: str, ctx: Context, language: str = "en", limit: int = 10):
        key = self._make_key(concept, language, limit)
        
        if key in self.cache:
            return self.cache[key]
        
        result = await related_concepts(concept, ctx, language, limit)
        
        # Manage cache size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = result
        return result

# Usage
cache = RelatedConceptsCache()
result = await cache.get_related("dog", context)
```

## Integration Examples

### FastMCP Tool Registration

```python
from fastmcp import FastMCP
from conceptnet_mcp.tools.related_concepts import related_concepts

mcp = FastMCP("ConceptNet Tools")

# Tool is automatically registered via decorator
# Available as "related_concepts" in MCP client
```

### Client Usage

```python
# Via MCP client
result = await client.call_tool("related_concepts", {
    "concept": "artificial intelligence",
    "language": "en",
    "limit": 15
})

# Access structured data
source = result.data["source_concept"]
related = result.data["related_concepts"]
summary = result.data["relationship_summary"]
```

### Knowledge Graph Visualization

```python
def create_graph_data(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert results to graph visualization format."""
    
    nodes = []
    edges = []
    
    # Add source node
    source = result["source_concept"]
    nodes.append({
        "id": source["uri"],
        "label": source["label"],
        "type": "source",
        "language": source["language"]
    })
    
    # Add related nodes and edges
    for item in result["related_concepts"]:
        concept = item["concept"]
        
        # Add node
        nodes.append({
            "id": concept["uri"],
            "label": concept["label"],
            "type": "related",
            "language": concept["language"]
        })
        
        # Add edge
        edges.append({
            "source": source["uri"],
            "target": concept["uri"],
            "relation": item["relation"],
            "weight": item["weight"],
            "direction": item["direction"]
        })
    
    return {"nodes": nodes, "edges": edges}

# Usage
result = await related_concepts("dog", context, limit=10)
graph_data = create_graph_data(result)
```

## Error Handling

### Common Error Types

#### Concept Not Found

```json
{
  "error": "ConceptNotFound",
  "message": "Concept 'xyz' not found in language 'en'",
  "concept": "xyz",
  "language": "en"
}
```

#### Invalid Limit

```json
{
  "error": "ValidationError",
  "message": "Limit must be between 1 and 50",
  "field": "limit",
  "value": 100
}
```

#### No Relationships Found

```json
{
  "error": "NoRelationshipsFound",
  "message": "No relationships found for concept 'obscure_term'",
  "concept": "obscure_term",
  "suggestions": [
    "Try a more common concept",
    "Check if concept exists with concept_lookup",
    "Use concept_query to find similar terms"
  ]
}
```

### Robust Error Handling

```python
async def robust_related_concepts(
    concept: str, 
    ctx: Context, 
    language: str = "en",
    limit: int = 10,
    fallback_strategies: bool = True
) -> Dict[str, Any]:
    """Get related concepts with fallback strategies."""
    
    try:
        return await related_concepts(concept, ctx, language, limit)
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "not found" in error_msg and fallback_strategies:
            # Try with concept_query to find similar concepts
            from conceptnet_mcp.tools.concept_query import concept_query
            
            try:
                query_result = await concept_query(concept, ctx, language, limit=5)
                if query_result["concepts"]:
                    # Try first result
                    first_concept = query_result["concepts"][0]["label"]
                    return await related_concepts(first_concept, ctx, language, limit)
            except:
                pass
        
        # Re-raise original error if fallbacks fail
        raise e
```

## Best Practices

### Input Validation

```python
def validate_related_concepts_input(
    concept: str, 
    language: str = "en", 
    limit: int = 10
) -> bool:
    """Validate input parameters."""
    
    if not concept or not concept.strip():
        raise ValueError("Concept cannot be empty")
    
    if len(concept) > 200:
        raise ValueError("Concept too long (max 200 characters)")
    
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise ValueError("Limit must be between 1 and 50")
    
    if len(language) != 2:
        raise ValueError("Language must be 2-character code")
    
    return True
```

### Result Processing

```python
def extract_concept_names(result: Dict[str, Any]) -> List[str]:
    """Extract just the concept names from results."""
    return [item["concept"]["label"] for item in result["related_concepts"]]

def get_strongest_relationships(result: Dict[str, Any], count: int = 5) -> List[Dict]:
    """Get the strongest relationships."""
    sorted_relations = sorted(
        result["related_concepts"],
        key=lambda x: x["weight"],
        reverse=True
    )
    return sorted_relations[:count]

def group_by_relation_type(result: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """Group relationships by type."""
    groups = {}
    for item in result["related_concepts"]:
        relation = item["relation"]
        if relation not in groups:
            groups[relation] = []
        groups[relation].append(item)
    return groups
```

### Performance Tips

1. **Use appropriate limits**: Don't request more relationships than needed
2. **Cache frequent requests**: Store results for commonly accessed concepts
3. **Batch related requests**: Use asyncio for multiple concurrent requests
4. **Filter early**: Apply filters to reduce data processing overhead

## Common Use Cases

### 1. Content Recommendation

Find related topics for content suggestions:

```python
async def suggest_related_topics(topic: str, ctx: Context) -> List[str]:
    """Suggest related topics for content creation."""
    result = await related_concepts(topic, ctx, limit=20)
    
    # Focus on strong relationships
    strong_relations = [
        item["concept"]["label"] 
        for item in result["related_concepts"]
        if item["weight"] > 6.0
    ]
    
    return strong_relations[:10]

# Usage
suggestions = await suggest_related_topics("machine learning", context)
```

### 2. Semantic Expansion

Expand search terms or tags:

```python
async def expand_tags(base_tag: str, ctx: Context) -> List[str]:
    """Expand a tag with semantically related terms."""
    result = await related_concepts(base_tag, ctx, limit=15)
    
    # Include original tag and related concepts
    expanded = [base_tag]
    expanded.extend([
        item["concept"]["label"] 
        for item in result["related_concepts"]
        if item["weight"] > 5.0
    ])
    
    return list(set(expanded))  # Remove duplicates

# Usage
expanded_tags = await expand_tags("sustainability", context)
```

### 3. Knowledge Graph Building

Build local knowledge graphs:

```python
async def build_concept_subgraph(
    root_concept: str,
    ctx: Context,
    max_depth: int = 2,
    max_breadth: int = 10
) -> Dict[str, Any]:
    """Build a subgraph around a concept."""
    
    graph = {"nodes": set(), "edges": []}
    to_process = [(root_concept, 0)]  # (concept, depth)
    processed = set()
    
    while to_process:
        concept, depth = to_process.pop(0)
        
        if concept in processed or depth >= max_depth:
            continue
            
        processed.add(concept)
        graph["nodes"].add(concept)
        
        try:
            result = await related_concepts(concept, ctx, limit=max_breadth)
            
            for item in result["related_concepts"]:
                related_concept = item["concept"]["label"]
                
                # Add edge
                graph["edges"].append({
                    "source": concept,
                    "target": related_concept,
                    "relation": item["relation"],
                    "weight": item["weight"]
                })
                
                # Queue for processing if within depth limit
                if depth + 1 < max_depth:
                    to_process.append((related_concept, depth + 1))
        
        except Exception as e:
            print(f"Error processing {concept}: {e}")
    
    return {
        "nodes": list(graph["nodes"]),
        "edges": graph["edges"]
    }

# Usage
subgraph = await build_concept_subgraph("artificial intelligence", context)
```

### 4. Educational Applications

Create learning paths and concept maps:

```python
async def create_learning_path(subject: str, ctx: Context) -> Dict[str, Any]:
    """Create a learning path for a subject."""
    result = await related_concepts(subject, ctx, limit=25)
    
    # Categorize by relationship type
    learning_path = {
        "prerequisites": [],  # IsA relationships (broader concepts)
        "core_concepts": [],  # SimilarTo and RelatedTo
        "applications": [],   # UsedFor relationships
        "details": []        # HasProperty, PartOf relationships
    }
    
    for item in result["related_concepts"]:
        concept_name = item["concept"]["label"]
        relation = item["relation"]
        
        if relation == "IsA" and item["direction"] == "outgoing":
            learning_path["prerequisites"].append(concept_name)
        elif relation in ["SimilarTo", "RelatedTo"]:
            learning_path["core_concepts"].append(concept_name)
        elif relation == "UsedFor":
            learning_path["applications"].append(concept_name)
        else:
            learning_path["details"].append(concept_name)
    
    return learning_path

# Usage
path = await create_learning_path("machine learning", context)
```

## Troubleshooting

### Common Issues

1. **No relationships found**: Concept may be too specific or poorly represented
2. **Unexpected relationships**: ConceptNet may have noisy or incorrect data
3. **Performance issues**: Large limit values can slow down responses
4. **Language coverage**: Less common languages may have limited relationships

### Debugging Techniques

```python
# Enable detailed logging
import logging
logging.getLogger("conceptnet_mcp").setLevel(logging.DEBUG)

# Test with known concepts first
test_result = await related_concepts("dog", context, limit=5)
print(f"Found {len(test_result['related_concepts'])} relationships")

# Check relationship quality
for item in test_result["related_concepts"]:
    print(f"{item['relation']}: {item['concept']['label']} (weight: {item['weight']})")
```

### Performance Monitoring

```python
import time

async def monitored_related_concepts(concept: str, ctx: Context, **kwargs):
    """Related concepts with performance monitoring."""
    start_time = time.time()
    
    try:
        result = await related_concepts(concept, ctx, **kwargs)
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # ms
        
        print(f"Query for '{concept}' took {execution_time:.1f}ms")
        print(f"Found {len(result['related_concepts'])} relationships")
        
        return result
        
    except Exception as e:
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        
        print(f"Query for '{concept}' failed after {execution_time:.1f}ms: {e}")
        raise
```

## Next Steps

- Use [Concept Lookup](concept_lookup.md) for detailed information about found concepts
- Apply [Concept Query](concept_query.md) to search for concepts by topic
- Calculate [Concept Relatedness](concept_relatedness.md) between related concepts
- Review the [API Reference](../api.md) for technical implementation details
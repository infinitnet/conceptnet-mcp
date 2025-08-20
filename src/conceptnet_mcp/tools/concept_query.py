"""
MCP tool for advanced ConceptNet querying with multiple filters.

This module implements the concept_query MCP tool that provides sophisticated
filtering capabilities for exploring ConceptNet's knowledge graph. It supports
multiple filter parameters and returns comprehensive results with analysis.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
import asyncio

from fastmcp import Context

from ..models.query import QueryFilters
from ..client.conceptnet_client import ConceptNetClient
from ..client.processor import ResponseProcessor
from ..utils.exceptions import (
    ConceptNetAPIError,
    ValidationError as MCPValidationError,
    InvalidConceptURIError,
    MCPToolError
)
from ..utils.text_utils import (
    normalize_concept_text,
    validate_language_code,
    construct_concept_uri,
    normalize_text_for_display
)


from ..utils.logging import get_logger


def create_concept_uri(term: str, language: str) -> str:
    """Create a ConceptNet URI from a term and language."""
    return construct_concept_uri(term, language)


logger = get_logger(__name__)


async def concept_query(
    ctx: Context,
    start: Optional[str] = None,
    end: Optional[str] = None,
    rel: Optional[str] = None,
    node: Optional[str] = None,
    other: Optional[str] = None,
    sources: Optional[str] = None,
    language: str = "en",
    limit_results: bool = False
) -> Dict[str, Any]:
    """
    Advanced querying of ConceptNet with multiple filters.
    
    This tool provides sophisticated filtering capabilities for exploring
    ConceptNet's knowledge graph. You can combine multiple filters to find
    specific types of relationships and concepts.
    
    Args:
        start: Start concept URI or term (e.g., "dog", "/c/en/dog")
        end: End concept URI or term (e.g., "animal", "/c/en/animal")
        rel: Relation type (e.g., "IsA", "/r/IsA")
        node: Concept that must be either start or end of edges
        other: Used with 'node' to find relationships between two specific concepts
        sources: Filter by data source (e.g., "wordnet", "/s/activity/omcs")
        language: Language filter for concepts (default: "en")
        limit_results: If True, limits to 20 results for quick queries (default: False)
        
    Returns:
        Comprehensive query results with edges, summaries, and metadata
        
    Examples:
        - concept_query(start="dog", rel="IsA") -> Find what dogs are
        - concept_query(end="vehicle", rel="IsA") -> Find types of vehicles
        - concept_query(node="car", other="transportation") -> Relationships between car and transportation
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log the incoming request
        await ctx.info(f"Starting advanced ConceptNet query with multiple filters")
        
        # 1. Parameter validation and conversion
        await ctx.info("Validating and processing query parameters...")
        validated_params = await _validate_and_convert_parameters(
            start, end, rel, node, other, sources, language, ctx
        )
        
        # 2. Build QueryFilters object
        filters = await _build_query_filters(validated_params, limit_results, ctx)
        
        # 3. Query ConceptNet API
        await ctx.info(f"Executing ConceptNet query: {filters}")
        
        async with ConceptNetClient() as client:
            try:
                response = await client.query_concepts(
                    filters=filters,
                    get_all_pages=not limit_results,
                    target_language=language if language != "en" else None
                )
            except ConceptNetAPIError as e:
                return _create_api_error_response(validated_params, str(e), start_time)
        
        # 4. Process and enhance response
        await ctx.info("Processing and enhancing query results...")
        processor = ResponseProcessor(default_language=language)
        
        # Process edges with same-language filtering by default
        edges = response.get("edges", [])
        # Apply same-language filtering by default
        filtered_edges = processor.filter_by_language(edges, language, require_both=True)
        processed_edges = processor.process_edge_list(filtered_edges, target_language=language)
        
        if len(filtered_edges) != len(edges):
            await ctx.info(f"Applied same-language filtering ({language}): {len(edges)} → {len(filtered_edges)} edges")
        
        # 5. Create comprehensive enhanced response
        enhanced_response = await _create_enhanced_query_response(
            processed_edges, response, validated_params, filters,
            language, limit_results, start_time, ctx
        )
        
        # Log completion
        total_edges = len(processed_edges)
        await ctx.info(f"Successfully completed query with {total_edges} results")
        
        return enhanced_response
        
    except MCPValidationError as e:
        return _create_validation_error_response(e, start_time)
        
    except ConceptNetAPIError as e:
        return _create_api_error_response({}, str(e), start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error in concept_query: {e}")
        return _create_unexpected_error_response(str(e), start_time)


async def _validate_and_convert_parameters(
    start: Optional[str],
    end: Optional[str], 
    rel: Optional[str],
    node: Optional[str],
    other: Optional[str],
    sources: Optional[str],
    language: str,
    ctx: Context
) -> Dict[str, Optional[str]]:
    """Validate and convert all query parameters to proper ConceptNet URIs."""
    
    # Validate at least one filter is provided (not None and not empty string)
    filter_params = [start, end, rel, node, sources]
    if all(param is None or param == '' for param in filter_params):
        raise MCPValidationError(
            "query_parameters",
            "all_none_or_empty",
            "At least one filter parameter (start, end, rel, node, sources) must be provided"
        )
    
    # Validate 'other' requires 'node'
    if other and not node:
        raise MCPValidationError(
            "other", 
            other, 
            "'other' parameter requires 'node' parameter to be set"
        )
    
    # Validate language
    if not validate_language_code(language):
        await ctx.warning(f"Language code '{language}' may not be supported by ConceptNet")
    
    validated = {}
    
    # Convert concept parameters to URIs if needed
    for param_name, param_value in [("start", start), ("end", end), ("node", node), ("other", other)]:
        if param_value is not None:
            # Check for empty strings - these should be validation errors
            if param_value == '':
                raise MCPValidationError(param_name, param_value, "Non-empty string")
            
            if param_value.startswith('/c/'):
                # Already a URI, validate format
                parts = param_value.split('/')
                if len(parts) < 4:
                    raise InvalidConceptURIError(param_value, "/c/language/term")
                validated[param_name] = param_value
            else:
                # Convert text to URI
                try:
                    validated[param_name] = create_concept_uri(param_value, language)
                    await ctx.debug(f"Converted {param_name}: '{param_value}' -> '{validated[param_name]}'")
                except Exception as e:
                    raise MCPValidationError(param_name, param_value, f"Valid concept term or URI: {e}")
        else:
            validated[param_name] = None
    
    # Convert relation parameter if needed
    if rel is not None:
        # Check for empty strings
        if rel == '':
            raise MCPValidationError("rel", rel, "Non-empty string")
            
        if rel.startswith('/r/'):
            # Already a relation URI
            validated["rel"] = rel
        else:
            # Convert text to relation URI
            # Handle common relation names and convert to proper format
            normalized_rel = rel.title().replace(' ', '').replace('_', '')
            validated["rel"] = f"/r/{normalized_rel}"
            await ctx.debug(f"Converted relation: '{rel}' -> '{validated['rel']}'")
    else:
        validated["rel"] = None
    
    # Handle sources parameter
    if sources is not None:
        # Check for empty strings
        if sources == '':
            raise MCPValidationError("sources", sources, "Non-empty string")
            
        if sources.startswith('/s/'):
            # Already a source URI
            validated["sources"] = sources
        else:
            # Convert text to source URI format (common sources)
            source_mappings = {
                "wordnet": "/s/resource/wordnet/rdf/3.1",
                "dbpedia": "/s/resource/dbpedia/2015/en",
                "omcs": "/s/activity/omcs",
                "conceptnet": "/s/resource/conceptnet/5.7"
            }
            
            if sources.lower() in source_mappings:
                validated["sources"] = source_mappings[sources.lower()]
                await ctx.debug(f"Converted source: '{sources}' -> '{validated['sources']}'")
            else:
                # Assume it's a custom source pattern
                validated["sources"] = sources if sources.startswith('/s/') else f"/s/{sources}"
    else:
        validated["sources"] = None
    
    return validated


async def _build_query_filters(
    validated_params: Dict[str, Optional[str]], 
    limit_results: bool,
    ctx: Context
) -> QueryFilters:
    """Build QueryFilters object from validated parameters."""
    
    try:
        filters = QueryFilters(
            start=validated_params["start"],
            end=validated_params["end"],
            rel=validated_params["rel"],
            node=validated_params["node"],
            other=validated_params["other"],
            sources=validated_params["sources"],
            limit=20 if limit_results else 1000,
            offset=0
        )
        
        # Log the filters being applied
        specified_filters = filters.get_specified_filters()
        await ctx.info(f"Applied filters: {', '.join(specified_filters)}")
        
        return filters
        
    except Exception as e:
        raise MCPValidationError("query_filters", str(validated_params), f"Valid query combination: {e}")


async def _create_enhanced_query_response(
    processed_edges: List[Dict[str, Any]],
    raw_response: Dict[str, Any],
    validated_params: Dict[str, Optional[str]],
    filters: QueryFilters,
    language: str,
    limit_results: bool,
    start_time: datetime,
    ctx: Context
) -> Dict[str, Any]:
    """Create comprehensive enhanced response with analysis and metadata."""
    
    # Prepare query information
    query_info = {
        "parameters_used": {k: v for k, v in validated_params.items() if v is not None},
        "filters_applied": list(filters.get_specified_filters()),
        "total_results": len(processed_edges),
        "pagination_used": not limit_results,
        "language_filter": language
    }
    
    # Analyze results
    analysis = await _analyze_query_results(processed_edges, ctx)
    
    # Create metadata
    execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    metadata = {
        "query_time": start_time.isoformat() + "Z",
        "execution_time_ms": round(execution_time),
        "api_calls_made": 1 if not limit_results else 1,  # May be more with pagination
        "results_processed": len(processed_edges),
        "filters_applied_count": len(filters.get_specified_filters())
    }
    
    # Build final response
    enhanced_response = {
        "query_info": query_info,
        "edges": processed_edges,
        "summary": analysis["summary"],
        "metadata": metadata
    }
    
    # Add examples and suggestions
    if processed_edges:
        enhanced_response["examples"] = await _generate_query_examples(validated_params, processed_edges[:3])
        enhanced_response["suggestions"] = await _generate_query_suggestions(validated_params, analysis)
    else:
        enhanced_response["suggestions"] = _generate_no_results_suggestions(validated_params)
    
    await ctx.info(f"Enhanced response created with {len(processed_edges)} edges and comprehensive analysis")
    
    return enhanced_response


async def _analyze_query_results(edges: List[Dict[str, Any]], ctx: Context) -> Dict[str, Any]:
    """Perform comprehensive analysis of query results."""
    
    if not edges:
        return {
            "summary": {
                "edges_by_relation": {},
                "unique_concepts": [],
                "weight_distribution": {"high": 0, "medium": 0, "low": 0},
                "data_sources": [],
                "concept_languages": [],
                "average_weight": 0.0
            }
        }
    
    # Analyze relations
    edges_by_relation = {}
    unique_concepts = set()
    weights = []
    data_sources = set()
    concept_languages = set()
    
    for edge in edges:
        # Relations
        rel = edge.get("rel", {})
        rel_name = rel.get("normalized_label") or rel.get("label") or "unknown"
        edges_by_relation[rel_name] = edges_by_relation.get(rel_name, 0) + 1
        
        # Concepts
        start = edge.get("start", {})
        end = edge.get("end", {})
        
        start_label = start.get("normalized_label") or start.get("label", "")
        end_label = end.get("normalized_label") or end.get("label", "")
        
        if start_label:
            unique_concepts.add(start_label)
        if end_label:
            unique_concepts.add(end_label)
        
        # Languages
        start_lang = start.get("language")
        end_lang = end.get("language")
        if start_lang:
            concept_languages.add(start_lang)
        if end_lang:
            concept_languages.add(end_lang)
        
        # Weights
        weight = edge.get("weight", 0)
        if weight:
            weights.append(weight)
        
        # Sources
        sources = edge.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if isinstance(source, dict):
                    source_id = source.get("@id", "")
                    if source_id:
                        data_sources.add(source_id)
    
    # Weight distribution
    weight_distribution = {"high": 0, "medium": 0, "low": 0}
    for weight in weights:
        if weight > 0.7:
            weight_distribution["high"] += 1
        elif weight > 0.3:
            weight_distribution["medium"] += 1
        else:
            weight_distribution["low"] += 1
    
    # Summary
    summary = {
        "edges_by_relation": dict(sorted(edges_by_relation.items(), key=lambda x: x[1], reverse=True)),
        "unique_concepts": sorted(list(unique_concepts))[:20],  # Top 20 concepts
        "weight_distribution": weight_distribution,
        "data_sources": sorted(list(data_sources)),
        "concept_languages": sorted(list(concept_languages)),
        "average_weight": round(sum(weights) / len(weights), 3) if weights else 0.0,
        "total_unique_concepts": len(unique_concepts),
        "most_common_relation": max(edges_by_relation, key=edges_by_relation.get) if edges_by_relation else None
    }
    
    await ctx.debug(f"Analysis complete: {len(edges)} edges, {len(unique_concepts)} unique concepts")
    
    return {"summary": summary}


async def _generate_query_examples(params: Dict[str, Optional[str]], sample_edges: List[Dict[str, Any]]) -> List[str]:
    """Generate example queries based on current parameters and results."""
    examples = []
    
    # Based on current parameters, suggest variations
    if params.get("start") and not params.get("rel"):
        examples.append(f"concept_query(start='{params['start']}', rel='IsA') -> Find what this concept is")
    
    if params.get("rel") and not params.get("start") and not params.get("end"):
        examples.append(f"concept_query(start='dog', rel='{params['rel']}') -> Apply this relation to 'dog'")
    
    # From sample edges, suggest new queries
    for edge in sample_edges[:2]:
        start = edge.get("start", {})
        end = edge.get("end", {})
        rel = edge.get("rel", {})
        
        start_label = start.get("normalized_label", "")
        end_label = end.get("normalized_label", "")
        rel_label = rel.get("normalized_label", "")
        
        if start_label and end_label:
            examples.append(f"concept_query(node='{start_label}', other='{end_label}') -> Explore '{start_label}' ↔ '{end_label}'")
    
    return examples[:3]  # Limit to 3 examples


async def _generate_query_suggestions(params: Dict[str, Optional[str]], analysis: Dict[str, Any]) -> List[str]:
    """Generate suggestions for further exploration."""
    suggestions = []
    summary = analysis.get("summary", {})
    
    # Suggest exploring top relations
    top_relations = list(summary.get("edges_by_relation", {}).keys())[:3]
    for rel in top_relations:
        suggestions.append(f"Explore more '{rel}' relationships by adding rel='{rel}' filter")
    
    # Suggest exploring concepts
    unique_concepts = summary.get("unique_concepts", [])[:3]
    for concept in unique_concepts:
        suggestions.append(f"Explore '{concept}' as a central concept using node='{concept}'")
    
    # Suggest different languages if multiple found
    languages = summary.get("concept_languages", [])
    if len(languages) > 1:
        suggestions.append(f"Try different languages: {', '.join(languages[:3])}")
    
    return suggestions[:5]  # Limit to 5 suggestions


def _generate_no_results_suggestions(params: Dict[str, Optional[str]]) -> List[str]:
    """Generate suggestions when no results are found."""
    return [
        "Try broader search terms or remove some filters",
        "Check if concept URIs and relation types are correct",
        "Consider using 'node' parameter for more flexible matching",
        "Try different language codes or remove language filters",
        "Use simpler or more common concept terms"
    ]


def _create_validation_error_response(error: MCPValidationError, start_time: datetime) -> Dict[str, Any]:
    """Create response for validation errors."""
    return {
        "error": "validation_error",
        "message": f"Validation error for field '{error.field}': {error.value} (expected: {error.expected})",
        "field": error.field,
        "value": error.value,
        "expected": error.expected,
        "query_time": start_time.isoformat() + "Z",
        "examples": [
            "concept_query(start='dog', rel='IsA')",
            "concept_query(node='car', other='vehicle')",
            "concept_query(end='animal', rel='IsA')"
        ]
    }


def _create_api_error_response(params: Dict[str, Any], error_message: str, start_time: datetime) -> Dict[str, Any]:
    """Create response for API errors."""
    return {
        "error": "api_error",
        "message": f"ConceptNet query failed: {error_message}",
        "query_parameters": params,
        "query_time": start_time.isoformat() + "Z",
        "suggestion": "The ConceptNet service may be temporarily unavailable. Please try again later."
    }


def _create_unexpected_error_response(error_message: str, start_time: datetime) -> Dict[str, Any]:
    """Create response for unexpected errors."""
    return {
        "error": "unexpected_error",
        "message": f"An unexpected error occurred: {error_message}",
        "query_time": start_time.isoformat() + "Z",
        "suggestion": "Please try again with simpler parameters or contact support if the error persists."
    }
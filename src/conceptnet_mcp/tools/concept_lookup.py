"""
MCP tool for looking up specific ConceptNet concepts.

This module implements the concept_lookup MCP tool that allows users to retrieve
detailed information about a specific concept by its URI or natural language term.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import asyncio

from fastmcp import Context

from ..client.conceptnet_client import ConceptNetClient
from ..client.processor import ResponseProcessor
from ..utils.exceptions import (
    ConceptNotFoundError, 
    ConceptNetAPIError,
    ValidationError as MCPValidationError,
    MCPToolError
)
from ..utils.text_utils import normalize_concept_text, validate_language_code
from ..utils.logging import get_logger


logger = get_logger(__name__)


async def concept_lookup(
    term: str,
    ctx: Context,
    language: str = "en",
    limit_results: bool = False,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Look up all edges for a specific concept in ConceptNet.
    
    This tool queries ConceptNet's knowledge graph to find all relationships
    and properties associated with a given concept. By default, it returns
    ALL results (not limited to 20) to provide comprehensive information.
    
    Args:
        term: The concept term to look up (e.g., "dog", "artificial intelligence")
        language: Language code for the concept (default: "en" for English)
        limit_results: If True, limits to first 20 results for quick queries (default: False)
        target_language: If specified, filters results to edges involving this language
        
    Returns:
        Comprehensive concept data including all related edges, relationship summaries,
        and metadata about the query results.
        
    Examples:
        - concept_lookup("dog") -> All relationships for "dog" in English
        - concept_lookup("perro", "es") -> All relationships for "perro" in Spanish
        - concept_lookup("cat", target_language="en") -> Only English-language cat relationships
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Log the incoming request
        await ctx.info(f"Looking up concept: '{term}' (language: {language})")
        
        # 1. Parameter validation
        await _validate_parameters(term, language, target_language, ctx)
        
        # 2. Normalize the input term
        normalized_term = normalize_concept_text(term, language)
        if normalized_term != term:
            await ctx.debug(f"Normalized term: '{term}' -> '{normalized_term}'")
        
        # 3. Query ConceptNet API
        await ctx.info(f"Querying ConceptNet API for concept '{normalized_term}'...")
        
        async with ConceptNetClient() as client:
            try:
                response = await client.get_concept(
                    term=normalized_term,
                    language=language,
                    get_all_pages=not limit_results,
                    target_language=target_language
                )
            except ConceptNotFoundError:
                return _create_not_found_response(term, language, normalized_term)
            except ConceptNetAPIError as e:
                return _create_api_error_response(term, language, str(e))
        
        # 4. Apply default language filtering if target_language not specified
        effective_target_language = target_language if target_language is not None else language
        
        # 5. Process and normalize the response
        processor = ResponseProcessor(default_language=language)
        processed_response = processor.process_concept_response(
            response, target_language=effective_target_language
        )
        
        # 6. Create enhanced response with summaries and metadata
        enhanced_response = await _create_enhanced_response(
            processed_response, term, normalized_term, language,
            effective_target_language, limit_results, start_time, ctx
        )
        
        # Log completion
        total_edges = enhanced_response.get("summary", {}).get("total_edges", 0)
        await ctx.info(f"Successfully retrieved {total_edges} edges for concept '{term}'")
        
        return enhanced_response
        
    except MCPValidationError as e:
        # Handle validation errors specifically
        return {
            "error": "validation_error",
            "message": f"Validation error for field '{e.field}': {e.value} (expected: {e.expected})",
            "field": e.field,
            "value": e.value,
            "expected": e.expected,
            "term": term,
            "language": language,
            "query_time": start_time.isoformat() + "Z"
        }
        
    except ConceptNotFoundError:
        return _create_not_found_response(term, language, term)
        
    except ConceptNetAPIError as e:
        return _create_api_error_response(term, language, str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in concept_lookup: {e}")
        return {
            "error": "unexpected_error",
            "message": f"An unexpected error occurred: {str(e)}",
            "term": term,
            "language": language,
            "query_time": start_time.isoformat() + "Z"
        }


async def _validate_parameters(
    term: str, 
    language: str, 
    target_language: Optional[str],
    ctx: Context
) -> None:
    """Validate all input parameters."""
    # Validate term
    if not term or not term.strip():
        raise MCPValidationError("term", term, "Non-empty string")
    
    if len(term.strip()) > 200:  # Reasonable length limit
        raise MCPValidationError("term", term, "Term length must be 200 characters or less")
    
    # Validate language
    if not language or not isinstance(language, str):
        raise MCPValidationError("language", language, "Valid language code (e.g., 'en', 'es')")
    
    if not validate_language_code(language):
        await ctx.warning(f"Language code '{language}' may not be supported by ConceptNet")
    
    # Validate target_language if provided
    if target_language:
        if not isinstance(target_language, str):
            raise MCPValidationError("target_language", target_language, "Valid language code or None")
        
        if not validate_language_code(target_language):
            await ctx.warning(f"Target language code '{target_language}' may not be supported by ConceptNet")


def _create_not_found_response(term: str, language: str, normalized_term: str) -> Dict[str, Any]:
    """Create a structured response for concept not found."""
    return {
        "error": "concept_not_found",
        "message": f"No concept found for term '{term}' in language '{language}'",
        "suggestions": [
            "Check the spelling of the term",
            "Try a different language code",
            "Use simpler or more common terms",
            "Consider using related terms or synonyms"
        ],
        "searched_term": term,
        "normalized_term": normalized_term,
        "language": language,
        "query_time": datetime.now(timezone.utc).isoformat() + "Z"
    }


def _create_api_error_response(term: str, language: str, error_message: str) -> Dict[str, Any]:
    """Create a structured response for API errors."""
    return {
        "error": "api_error",
        "message": f"ConceptNet API error: {error_message}",
        "details": "The ConceptNet service may be temporarily unavailable. Please try again later.",
        "term": term,
        "language": language,
        "query_time": datetime.now(timezone.utc).isoformat() + "Z"
    }


async def _create_enhanced_response(
    processed_response: Dict[str, Any],
    original_term: str,
    normalized_term: str,
    language: str,
    target_language: str,
    limit_results: bool,
    start_time: datetime,
    ctx: Context
) -> Dict[str, Any]:
    """Create an enhanced response with summaries and metadata."""
    
    # Extract edges and basic info
    edges = processed_response.get("edges", [])
    concept_info = {
        "term": normalized_term,
        "original_term": original_term,
        "language": language,
        "uri": processed_response.get("@id", f"/c/{language}/{normalized_term}"),
        "normalized_display": processed_response.get("normalized_id", original_term)
    }
    
    # Create summary statistics
    processor = ResponseProcessor(default_language=language)
    edge_stats = processor.get_edge_statistics(edges)
    
    # Count relations by type
    relation_counts = {}
    top_relations = []
    for edge in edges:
        rel = edge.get("rel", {})
        rel_name = rel.get("normalized_label") or rel.get("label") or "unknown"
        relation_counts[rel_name] = relation_counts.get(rel_name, 0) + 1
    
    # Get top 5 most common relations
    if relation_counts:
        top_relations = sorted(relation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_relations = [rel_name for rel_name, count in top_relations]
    
    # Create the enhanced response
    enhanced_response = {
        "concept": concept_info,
        "edges": edges,
        "summary": {
            "total_edges": len(edges),
            "edge_count_by_relation": relation_counts,
            "languages_found": list(edge_stats.get("languages", [])),
            "top_relations": top_relations,
            "average_weight": round(edge_stats.get("avg_weight", 0.0), 3),
            "weight_range": edge_stats.get("weight_range", (0.0, 0.0)),
            "most_common_relation": edge_stats.get("most_common_relation")
        },
        "metadata": {
            "query_time": start_time.isoformat() + "Z",
            "total_results": len(edges),
            "pagination_used": not limit_results,
            "language_filtered": True,
            "original_term": original_term,
            "normalized_term": normalized_term,
            "search_language": language,
            "target_language": target_language
        }
    }
    
    # Add language filtering info
    original_count = processed_response.get("_original_edge_count")
    if original_count and original_count != len(edges):
        enhanced_response["metadata"]["edges_before_filtering"] = original_count
        enhanced_response["metadata"]["edges_after_filtering"] = len(edges)
        await ctx.info(f"Language filtering applied ({target_language}): {original_count} -> {len(edges)} edges")
    
    # Add pagination info
    if not limit_results:
        await ctx.info("Retrieved complete results using pagination")
    else:
        await ctx.info("Limited results to first page (20 results)")
    
    return enhanced_response
"""
MCP tool for finding concepts semantically related to a given concept.

This module implements the related_concepts FastMCP tool that uses ConceptNet's 
/related endpoint to find concepts that are semantically similar to a given input
concept, with support for language filtering, similarity analysis, and comprehensive
response enhancement.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio
import statistics

from fastmcp import Context

from ..client.conceptnet_client import ConceptNetClient
from ..client.processor import ResponseProcessor
from ..utils.exceptions import (
    ConceptNotFoundError, 
    ConceptNetAPIError,
    ValidationError as MCPValidationError,
    MCPToolError
)
from ..utils.text_utils import (
    normalize_concept_text, 
    validate_language_code,
    normalize_text_for_display,
    extract_language_from_uri,
    normalize_uri_to_text
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


def _clean_concept_term(term: str) -> str:
    """
    Clean concept terms by removing WordNet and POS tag annotations.
    
    Removes technical annotations like /Wn/Food, /Wn/Substance, /N, /V, etc.
    that are used internally by ConceptNet but should not appear
    in user-facing results.
    
    Args:
        term: Original concept term that may contain POS tags
        
    Returns:
        Cleaned term without POS tag annotations
    """
    if not term or not isinstance(term, str):
        return term
    
    # Remove WordNet-derived tags like /Wn/Food, /Wn/Substance, etc.
    # Pattern matches: /Wn/ followed by any word characters
    import re
    wn_pattern = r'/Wn/[\w]*'
    cleaned = re.sub(wn_pattern, '', term)
    
    # Remove part-of-speech tags like /N, /V, /A, /ADJ, /ADV, etc.
    # Pattern matches: slash followed by uppercase letters/common POS tags
    pos_pattern = r'/[A-Z][A-Z]*\b'
    cleaned = re.sub(pos_pattern, '', cleaned)
    
    # Remove trailing slashes (edge case)
    cleaned = re.sub(r'/$', '', cleaned)
    
    # Clean up any remaining whitespace
    cleaned = cleaned.strip()
    
    return cleaned if cleaned else term


async def related_concepts(
    term: str,
    ctx: Context,
    language: str = "en",
    filter_language: Optional[str] = None,
    limit: int = 100,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Find concepts semantically related to the given concept.
    
    This tool uses ConceptNet's semantic similarity algorithms to find
    concepts that are related to the input term. Results are ranked by
    similarity score and can be filtered by language. By default, returns
    a minimal format optimized for LLM consumption.
    
    Args:
        term: The concept term to find related concepts for (e.g., "dog", "happiness")
        language: Language code for the input term (default: "en" for English)
        filter_language: Language to filter results to (default: None, which defaults to "en" for English)
        limit: Maximum number of related concepts to return (default: 100, max: 100)
        verbose: If True, returns detailed format with full metadata (default: False)
        
    Returns:
        Related concepts with similarity scores (minimal format) or
        comprehensive analysis with statistical metadata (verbose format).
        
    Examples:
        - related_concepts("dog") -> Minimal format with similarity scores
        - related_concepts("dog", verbose=True) -> Full detailed format with analysis
        - related_concepts("perro", "es") -> Spanish concepts related to "perro"
        - related_concepts("cat", limit=10) -> Top 10 concepts related to "cat"
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Default filter_language to "en" if not provided
        if filter_language is None:
            filter_language = "en"
            
        # Log the incoming request
        await ctx.info(f"Finding related concepts for: '{term}' (language: {language})")
        
        # 1. Parameter validation
        await _validate_parameters(term, language, filter_language, limit, ctx)
        
        # 2. Normalize the input term
        normalized_term = normalize_concept_text(term, language)
        if normalized_term != term:
            await ctx.debug(f"Normalized term: '{term}' -> '{normalized_term}'")
        
        # 3. Query ConceptNet API for related concepts
        await ctx.info(f"Querying ConceptNet /related endpoint for '{normalized_term}'...")
        
        async with ConceptNetClient() as client:
            try:
                response = await client.get_related(
                    term=normalized_term,
                    language=language,
                    filter_language=filter_language,
                    limit=limit
                )
            except ConceptNotFoundError:
                return _create_not_found_response(term, language, normalized_term)
            except ConceptNetAPIError as e:
                return _create_api_error_response(term, language, str(e))
        
        # 4. Return appropriate format based on verbose parameter
        if verbose:
            # Return detailed format with full metadata (existing behavior)
            enhanced_response = await _create_enhanced_response(
                response, term, normalized_term, language, filter_language,
                limit, start_time, ctx
            )
            
            total_found = enhanced_response.get("summary", {}).get("total_found", 0)
            await ctx.info(f"Successfully found {total_found} related concepts for '{term}' (verbose format)")
            
            return enhanced_response
        else:
            # Return minimal format optimized for LLMs
            # Create a mock processed response for the minimal formatter
            mock_response = {"related_concepts": []}
            
            # Process raw related concepts data
            related_concepts_raw = response.get("related", [])
            for i, concept_data in enumerate(related_concepts_raw):
                concept_id = concept_data.get("@id", "")
                weight = concept_data.get("weight", 0.0)
                
                # Extract term from URI
                term_text = ""
                if concept_id:
                    parts = concept_id.split('/')
                    if len(parts) >= 4 and parts[1] == 'c':
                        raw_term = parts[3].replace('_', ' ')
                        # Apply POS tag filtering to remove "/Wn/..." patterns
                        term_text = _clean_concept_term(raw_term)
                
                if term_text:
                    mock_response["related_concepts"].append({
                        "concept": {
                            "term": term_text,
                            "normalized_display": term_text
                        },
                        "similarity": {
                            "score": weight
                        }
                    })
            
            minimal_response = ResponseProcessor().create_minimal_related_response(
                mock_response, term
            )
            
            total_found = minimal_response.get("summary", {}).get("total_found", 0)
            await ctx.info(f"Successfully found {total_found} related concepts for '{term}' (minimal format)")
            
            return minimal_response
        
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
        logger.error(f"Unexpected error in related_concepts: {e}")
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
    filter_language: Optional[str],
    limit: int,
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
    
    # Validate filter_language if provided
    if filter_language:
        if not isinstance(filter_language, str):
            raise MCPValidationError("filter_language", filter_language, "Valid language code or None")
        
        if not validate_language_code(filter_language):
            await ctx.warning(f"Filter language code '{filter_language}' may not be supported by ConceptNet")
    
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise MCPValidationError("limit", limit, "Integer between 1 and 100")


def _create_not_found_response(term: str, language: str, normalized_term: str) -> Dict[str, Any]:
    """Create a structured response for concept not found."""
    return {
        "error": "concept_not_found",
        "message": f"No related concepts found for '{term}' in language '{language}'",
        "suggestions": [
            "Check the spelling of the term",
            "Try a more common or general term",
            "Try a different language code",
            "Consider using synonyms or related terms"
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
        "message": f"ConceptNet related concepts API error: {error_message}",
        "details": "The service may be temporarily unavailable",
        "term": term,
        "language": language,
        "query_time": datetime.now(timezone.utc).isoformat() + "Z"
    }


async def _create_enhanced_response(
    response: Dict[str, Any],
    original_term: str,
    normalized_term: str,
    language: str,
    filter_language: Optional[str],
    limit: int,
    start_time: datetime,
    ctx: Context
) -> Dict[str, Any]:
    """Create an enhanced response with comprehensive analysis."""
    
    # Extract related concepts from response
    related_concepts_raw = response.get("related", [])
    
    if not related_concepts_raw:
        await ctx.info("No related concepts found in response")
        return _create_empty_response(original_term, normalized_term, language, filter_language, limit, start_time)
    
    # Process each related concept
    related_concepts = []
    similarity_scores = []
    languages_found = set()
    
    await ctx.info(f"Processing {len(related_concepts_raw)} related concepts...")
    
    for i, concept_data in enumerate(related_concepts_raw):
        try:
            processed_concept = _process_concept_data(concept_data, i + 1)
            related_concepts.append(processed_concept)
            
            # Collect statistics
            similarity_scores.append(processed_concept["similarity"]["score"])
            concept_lang = processed_concept["concept"]["language"]
            if concept_lang:
                languages_found.add(concept_lang)
                
        except Exception as e:
            await ctx.warning(f"Failed to process concept data: {e}")
            continue
    
    # Apply language filtering (use filter_language if specified, otherwise default to same language)
    target_lang = filter_language if filter_language is not None else language
    
    if target_lang and related_concepts:
        original_count = len(related_concepts)
        related_concepts = [
            concept for concept in related_concepts
            if concept["concept"]["language"] == target_lang
        ]
        if len(related_concepts) != original_count:
            await ctx.info(f"Language filtering applied ({target_lang}): {original_count} -> {len(related_concepts)} concepts")
    
    # Update similarity scores after filtering
    if related_concepts:
        similarity_scores = [concept["similarity"]["score"] for concept in related_concepts]
    
    # Create comprehensive summary
    summary = _create_summary_statistics(
        related_concepts, similarity_scores, languages_found, original_term
    )
    
    # Create query info
    query_info = {
        "input_term": original_term,
        "normalized_term": normalized_term,
        "input_language": language,
        "filter_language": filter_language,
        "requested_limit": limit,
        "actual_results": len(related_concepts)
    }
    
    # Create metadata
    end_time = datetime.now(timezone.utc)
    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    metadata = {
        "query_time": start_time.isoformat() + "Z",
        "execution_time_ms": execution_time_ms,
        "endpoint_used": f"/related/c/{language}/{normalized_term}",
        "language_filtering_applied": filter_language is not None
    }
    
    await ctx.info(f"Enhanced response created with {len(related_concepts)} concepts")
    
    return {
        "query_info": query_info,
        "related_concepts": related_concepts,
        "summary": summary,
        "metadata": metadata
    }


def _process_concept_data(concept_data: Dict[str, Any], rank: int) -> Dict[str, Any]:
    """Process a single related concept from the API response."""
    
    # Extract concept information
    concept_id = concept_data.get("@id", "")
    weight = concept_data.get("weight", 0.0)
    
    # Parse concept URI to extract term and language
    concept_term = ""
    concept_language = ""
    
    if concept_id:
        try:
            # Extract from URI like /c/en/cat
            parts = concept_id.split('/')
            if len(parts) >= 4 and parts[1] == 'c':
                concept_language = parts[2]
                concept_term = '/'.join(parts[3:])  # Handle multi-part terms
                concept_term = normalize_uri_to_text(concept_id)  # Convert to readable format
        except Exception:
            concept_term = concept_id
    
    # Categorize similarity score
    similarity_description = _categorize_similarity_score(weight)
    
    # Try to infer relationship context (basic heuristics)
    relationship_context = _infer_relationship_context(concept_term)
    
    return {
        "concept": {
            "term": concept_term,
            "language": concept_language,
            "uri": concept_id,
            "normalized_display": concept_term
        },
        "similarity": {
            "score": round(weight, 4),
            "description": similarity_description,
            "rank": rank
        },
        "relationship_context": relationship_context
    }


def _categorize_similarity_score(score: float) -> str:
    """Categorize a similarity score into descriptive categories."""
    if score >= 0.8:
        return "very strong"
    elif score >= 0.6:
        return "strong"
    elif score >= 0.4:
        return "moderate"
    elif score >= 0.2:
        return "weak"
    else:
        return "very weak"


def _infer_relationship_context(concept_term: str) -> str:
    """Provide basic context about why concepts might be related."""
    # This is a simple heuristic-based approach
    # In a more sophisticated implementation, this could use additional ConceptNet data
    return f"Semantically related to the query concept"


def _create_summary_statistics(
    related_concepts: List[Dict[str, Any]], 
    similarity_scores: List[float],
    languages_found: set,
    original_term: str
) -> Dict[str, Any]:
    """Create comprehensive statistical summary of the results."""
    
    if not similarity_scores:
        return {
            "total_found": 0,
            "languages_in_results": [],
            "similarity_range": {"highest": 0.0, "lowest": 0.0, "average": 0.0},
            "categories": {"very_strong": 0, "strong": 0, "moderate": 0, "weak": 0, "very_weak": 0}
        }
    
    # Calculate similarity statistics
    highest_score = max(similarity_scores)
    lowest_score = min(similarity_scores)
    average_score = statistics.mean(similarity_scores)
    
    # Categorize similarity scores
    categories = {"very_strong": 0, "strong": 0, "moderate": 0, "weak": 0, "very_weak": 0}
    for score in similarity_scores:
        category = _categorize_similarity_score(score)
        if category == "very strong":
            categories["very_strong"] += 1
        elif category == "strong":
            categories["strong"] += 1
        elif category == "moderate":
            categories["moderate"] += 1
        elif category == "weak":
            categories["weak"] += 1
        else:
            categories["very_weak"] += 1
    
    return {
        "total_found": len(related_concepts),
        "languages_in_results": sorted(list(languages_found)),
        "similarity_range": {
            "highest": round(highest_score, 4),
            "lowest": round(lowest_score, 4),
            "average": round(average_score, 4)
        },
        "categories": categories
    }


def _create_empty_response(
    original_term: str,
    normalized_term: str, 
    language: str,
    filter_language: Optional[str],
    limit: int,
    start_time: datetime
) -> Dict[str, Any]:
    """Create response for when no related concepts are found."""
    
    query_info = {
        "input_term": original_term,
        "normalized_term": normalized_term,
        "input_language": language,
        "filter_language": filter_language,
        "requested_limit": limit,
        "actual_results": 0
    }
    
    summary = {
        "total_found": 0,
        "languages_in_results": [],
        "similarity_range": {"highest": 0.0, "lowest": 0.0, "average": 0.0},
        "categories": {"very_strong": 0, "strong": 0, "moderate": 0, "weak": 0, "very_weak": 0}
    }
    
    end_time = datetime.now(timezone.utc)
    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    metadata = {
        "query_time": start_time.isoformat() + "Z",
        "execution_time_ms": execution_time_ms,
        "endpoint_used": f"/related/c/{language}/{normalized_term}",
        "language_filtering_applied": filter_language is not None
    }
    
    return {
        "query_info": query_info,
        "related_concepts": [],
        "summary": summary,
        "metadata": metadata
    }
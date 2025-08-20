"""
MCP tool for calculating semantic relatedness between concepts.

This module implements the concept_relatedness MCP tool that computes semantic
similarity scores between pairs of concepts using ConceptNet's relatedness API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio
import time

from fastmcp import Context, FastMCP

from ..client.conceptnet_client import ConceptNetClient
from ..utils.exceptions import (
    ConceptNotFoundError,
    ConceptNetAPIError,
    ValidationError as MCPValidationError,
    MCPToolError
)
from ..utils.text_utils import normalize_concept_text, validate_language_code, construct_concept_uri
from ..utils.logging import get_logger


logger = get_logger(__name__)

# Create FastMCP instance for tool registration
mcp = FastMCP("ConceptNet Relatedness Tools")


async def concept_relatedness(
    concept1: str,
    concept2: str,
    ctx: Context,
    language1: str = "en",
    language2: str = "en"
) -> Dict[str, Any]:
    """
    Calculate semantic relatedness score between two concepts.
    
    This tool uses ConceptNet's semantic embeddings to calculate how
    related two concepts are to each other. The score ranges from 0.0
    (completely unrelated) to 1.0 (very strongly related).
    
    Args:
        concept1: First concept term for comparison (e.g., "dog", "happiness")
        concept2: Second concept term for comparison (e.g., "cat", "joy")
        language1: Language code for first concept (default: "en")
        language2: Language code for second concept (default: "en")
        
    Returns:
        Comprehensive relatedness analysis including numeric score,
        descriptive interpretation, relationship analysis, and metadata.
        
    Examples:
        - concept_relatedness("dog", "cat") -> Compare semantic similarity of dog and cat
        - concept_relatedness("perro", "dog", "es", "en") -> Cross-language comparison
        - concept_relatedness("happy", "sad") -> Compare emotional concepts
        - concept_relatedness("car", "bicycle") -> Compare transportation concepts
    """
    start_time = datetime.now(timezone.utc)
    execution_start = time.time()
    
    try:
        # Log the incoming request
        await ctx.info(f"Calculating relatedness between '{concept1}' ({language1}) and '{concept2}' ({language2})")
        
        # 1. Parameter validation
        validation_result = await _validate_parameters(concept1, concept2, language1, language2, ctx)
        if validation_result:
            return validation_result  # Return error response if validation failed
        
        # 2. Check for identical concepts
        identical_result = await _check_identical_concepts(concept1, concept2, language1, language2, start_time)
        if identical_result:
            return identical_result
        
        # 3. Normalize concept terms
        normalized_concept1 = normalize_concept_text(concept1, language1)
        normalized_concept2 = normalize_concept_text(concept2, language2)
        
        if normalized_concept1 != concept1:
            await ctx.debug(f"Normalized concept1: '{concept1}' -> '{normalized_concept1}'")
        if normalized_concept2 != concept2:
            await ctx.debug(f"Normalized concept2: '{concept2}' -> '{normalized_concept2}'")
        
        # 4. Query ConceptNet relatedness API
        await ctx.info(f"Querying ConceptNet relatedness API...")
        
        async with ConceptNetClient() as client:
            try:
                response = await client.get_relatedness(
                    concept1=normalized_concept1,
                    concept2=normalized_concept2,
                    language1=language1,
                    language2=language2
                )
            except ConceptNotFoundError as e:
                return _create_concept_not_found_response(concept1, concept2, language1, language2, str(e), start_time)
            except ConceptNetAPIError as e:
                return _create_api_error_response(concept1, concept2, language1, language2, str(e), start_time)
        
        # 5. Process and enhance the response
        execution_time_ms = int((time.time() - execution_start) * 1000)
        
        enhanced_response = await _create_enhanced_response(
            response, concept1, concept2, normalized_concept1, normalized_concept2,
            language1, language2, start_time, execution_time_ms, ctx
        )
        
        # Log completion
        score = enhanced_response.get("relatedness", {}).get("score", 0.0)
        description = enhanced_response.get("relatedness", {}).get("description", "unknown")
        await ctx.info(f"Relatedness calculated: {score:.3f} ({description})")
        
        return enhanced_response
        
    except MCPValidationError as e:
        # Handle validation errors specifically
        return {
            "error": "validation_error",
            "message": f"Validation error for field '{e.field}': {e.value} (expected: {e.expected})",
            "field": e.field,
            "value": e.value,
            "expected": e.expected,
            "concepts": {
                "concept1": concept1,
                "concept2": concept2,
                "language1": language1,
                "language2": language2
            },
            "query_time": start_time.isoformat() + "Z"
        }
        
    except ConceptNotFoundError as e:
        return _create_concept_not_found_response(concept1, concept2, language1, language2, str(e), start_time)
        
    except ConceptNetAPIError as e:
        return _create_api_error_response(concept1, concept2, language1, language2, str(e), start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error in concept_relatedness: {e}")
        return {
            "error": "unexpected_error",
            "message": f"An unexpected error occurred: {str(e)}",
            "concepts": {
                "concept1": concept1,
                "concept2": concept2,
                "language1": language1,
                "language2": language2
            },
            "query_time": start_time.isoformat() + "Z"
        }


async def _validate_parameters(
    concept1: str, 
    concept2: str, 
    language1: str, 
    language2: str,
    ctx: Context
) -> Optional[Dict[str, Any]]:
    """Validate all input parameters and return error response if invalid."""
    
    # Validate concept1
    if not concept1 or not concept1.strip():
        return {
            "error": "validation_error",
            "message": "concept1 parameter is required and cannot be empty",
            "field": "concept1",
            "suggestions": ["Provide a meaningful concept term"]
        }
    
    # Validate concept2
    if not concept2 or not concept2.strip():
        return {
            "error": "validation_error",
            "message": "concept2 parameter is required and cannot be empty",
            "field": "concept2",
            "suggestions": ["Provide a meaningful concept term"]
        }
    
    # Validate concept length
    if len(concept1.strip()) > 200:
        return {
            "error": "validation_error",
            "message": "concept1 length must be 200 characters or less",
            "field": "concept1",
            "value": len(concept1.strip()),
            "expected": "200 characters or less"
        }
    
    if len(concept2.strip()) > 200:
        return {
            "error": "validation_error",
            "message": "concept2 length must be 200 characters or less",
            "field": "concept2",
            "value": len(concept2.strip()),
            "expected": "200 characters or less"
        }
    
    # Validate language codes
    if not language1 or not isinstance(language1, str):
        return {
            "error": "validation_error",
            "message": "language1 must be a valid language code",
            "field": "language1",
            "suggestions": ["Use 2-3 letter language codes like 'en', 'es', 'fr'"]
        }
    
    if not language2 or not isinstance(language2, str):
        return {
            "error": "validation_error",
            "message": "language2 must be a valid language code",
            "field": "language2",
            "suggestions": ["Use 2-3 letter language codes like 'en', 'es', 'fr'"]
        }
    
    # Warn about potentially unsupported language codes
    if not validate_language_code(language1):
        await ctx.warning(f"Language code '{language1}' may not be supported by ConceptNet")
    
    if not validate_language_code(language2):
        await ctx.warning(f"Language code '{language2}' may not be supported by ConceptNet")
    
    return None  # No validation errors


async def _check_identical_concepts(
    concept1: str, 
    concept2: str, 
    language1: str, 
    language2: str,
    start_time: datetime
) -> Optional[Dict[str, Any]]:
    """Check if concepts are identical and return appropriate response."""
    
    # Normalize for comparison
    norm1 = normalize_concept_text(concept1, language1)
    norm2 = normalize_concept_text(concept2, language2)
    
    if norm1.lower() == norm2.lower() and language1 == language2:
        return {
            "query_info": {
                "concept1": {
                    "term": concept1,
                    "normalized": norm1,
                    "language": language1,
                    "uri": construct_concept_uri(norm1, language1)
                },
                "concept2": {
                    "term": concept2,
                    "normalized": norm2,
                    "language": language2,
                    "uri": construct_concept_uri(norm2, language2)
                },
                "comparison_type": "identical"
            },
            "relatedness": {
                "score": 1.0,
                "description": "identical",
                "interpretation": "These are the same concept",
                "percentile": 100,
                "confidence": "perfect"
            },
            "analysis": {
                "relationship_strength": "identical",
                "likely_connections": ["These concepts refer to the same entity"],
                "semantic_distance": 0.0,
                "similarity_category": "identical",
                "note": "Concepts are identical or very similar"
            },
            "metadata": {
                "query_time": start_time.isoformat() + "Z",
                "execution_time_ms": 0,
                "endpoint_used": "local_comparison",
                "calculation_method": "text_normalization"
            }
        }
    
    return None


def _create_concept_not_found_response(
    concept1: str, 
    concept2: str, 
    language1: str, 
    language2: str, 
    error_message: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Create a structured response for concept not found errors."""
    return {
        "error": "concept_not_found",
        "message": f"One or both concepts not found in ConceptNet: {error_message}",
        "suggestions": [
            "Check spelling of both concepts",
            "Try more common or general terms",
            "Verify language codes are correct",
            "Consider using synonyms or related terms"
        ],
        "concepts": {
            "concept1": concept1,
            "concept2": concept2,
            "language1": language1,
            "language2": language2
        },
        "query_time": start_time.isoformat() + "Z"
    }


def _create_api_error_response(
    concept1: str, 
    concept2: str, 
    language1: str, 
    language2: str, 
    error_message: str,
    start_time: datetime
) -> Dict[str, Any]:
    """Create a structured response for API errors."""
    return {
        "error": "api_error",
        "message": f"ConceptNet relatedness API error: {error_message}",
        "concepts": {
            "concept1": concept1,
            "concept2": concept2,
            "language1": language1,
            "language2": language2
        },
        "details": "The relatedness calculation service may be temporarily unavailable",
        "query_time": start_time.isoformat() + "Z"
    }


async def _create_enhanced_response(
    api_response: Dict[str, Any],
    original_concept1: str,
    original_concept2: str,
    normalized_concept1: str,
    normalized_concept2: str,
    language1: str,
    language2: str,
    start_time: datetime,
    execution_time_ms: int,
    ctx: Context
) -> Dict[str, Any]:
    """Create an enhanced response with analysis and metadata."""
    
    # Extract the relatedness score
    score = api_response.get('value', 0.0)
    
    # Create concept URIs
    uri1 = construct_concept_uri(normalized_concept1, language1)
    uri2 = construct_concept_uri(normalized_concept2, language2)
    
    # Determine comparison type
    comparison_type = "cross_language" if language1 != language2 else "same_language"
    
    # Get score interpretation
    description = _get_score_description(score)
    interpretation = _get_score_interpretation(score)
    confidence = _get_confidence_level(score)
    percentile = _estimate_percentile(score)
    
    # Perform relationship analysis
    analysis = await _analyze_relationship(
        original_concept1, original_concept2, score, language1, language2, ctx
    )
    
    return {
        "query_info": {
            "concept1": {
                "term": original_concept1,
                "normalized": normalized_concept1,
                "language": language1,
                "uri": uri1
            },
            "concept2": {
                "term": original_concept2,
                "normalized": normalized_concept2,
                "language": language2,
                "uri": uri2
            },
            "comparison_type": comparison_type
        },
        "relatedness": {
            "score": round(score, 4),
            "description": description,
            "interpretation": interpretation,
            "percentile": percentile,
            "confidence": confidence
        },
        "analysis": analysis,
        "metadata": {
            "query_time": start_time.isoformat() + "Z",
            "execution_time_ms": execution_time_ms,
            "endpoint_used": "/relatedness",
            "calculation_method": "conceptnet_embeddings"
        }
    }


def _get_score_description(score: float) -> str:
    """Convert numeric score to descriptive category."""
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


def _get_score_interpretation(score: float) -> str:
    """Provide human-readable interpretation of the score."""
    if score >= 0.8:
        return "These concepts are very strongly related"
    elif score >= 0.6:
        return "These concepts are strongly related"
    elif score >= 0.4:
        return "These concepts are moderately related"
    elif score >= 0.2:
        return "These concepts are weakly related"
    else:
        return "These concepts are very weakly related or unrelated"


def _get_confidence_level(score: float) -> str:
    """Determine confidence level based on score magnitude."""
    if score >= 0.7 or score <= 0.1:
        return "high"
    elif score >= 0.3:
        return "medium"
    else:
        return "low"


def _estimate_percentile(score: float) -> int:
    """Estimate percentile ranking compared to typical concept pairs."""
    # Based on ConceptNet distribution patterns
    if score >= 0.8:
        return 95
    elif score >= 0.6:
        return 85
    elif score >= 0.4:
        return 70
    elif score >= 0.2:
        return 50
    elif score >= 0.1:
        return 30
    else:
        return 15


async def _analyze_relationship(
    concept1: str,
    concept2: str,
    score: float,
    language1: str,
    language2: str,
    ctx: Context
) -> Dict[str, Any]:
    """Analyze the relationship between concepts and provide insights."""
    
    # Base analysis
    relationship_strength = _get_score_description(score)
    semantic_distance = round(1.0 - score, 4)
    similarity_category = _get_similarity_category(score)
    
    # Generate likely connections based on score
    likely_connections = _generate_likely_connections(concept1, concept2, score)
    
    analysis = {
        "relationship_strength": relationship_strength,
        "likely_connections": likely_connections,
        "semantic_distance": semantic_distance,
        "similarity_category": similarity_category
    }
    
    # Add cross-language analysis if applicable
    if language1 != language2:
        analysis["cross_language_note"] = f"Comparing {language1} concept with {language2} concept"
        analysis["translation_consideration"] = "Score may be affected by translation differences"
        await ctx.info(f"Cross-language comparison: {language1} vs {language2}")
    
    # Add contextual notes based on score
    if score >= 0.8:
        analysis["note"] = "Very high relatedness suggests strong semantic or categorical relationship"
    elif score <= 0.1:
        analysis["note"] = "Very low relatedness suggests concepts are likely unrelated"
    elif 0.4 <= score <= 0.6:
        analysis["note"] = "Moderate relatedness suggests indirect or domain-specific relationship"
    
    return analysis


def _get_similarity_category(score: float) -> str:
    """Categorize similarity level."""
    if score >= 0.7:
        return "high_similarity"
    elif score >= 0.4:
        return "medium_similarity"
    elif score >= 0.2:
        return "low_similarity"
    else:
        return "minimal_similarity"


def _generate_likely_connections(concept1: str, concept2: str, score: float) -> List[str]:
    """Generate likely connection explanations based on the score and concepts."""
    
    connections = []
    
    if score >= 0.8:
        connections = [
            "Concepts likely share the same category or domain",
            "May have direct hierarchical relationship",
            "Could be synonyms or very closely related terms",
            "Often used in similar contexts"
        ]
    elif score >= 0.6:
        connections = [
            "Concepts likely belong to related categories",
            "May share common properties or functions",
            "Could be connected through common usage patterns",
            "May appear together in similar contexts"
        ]
    elif score >= 0.4:
        connections = [
            "Concepts may share some common properties",
            "Could be indirectly related through broader categories",
            "May appear in related but distinct contexts",
            "Could have weak associative connections"
        ]
    elif score >= 0.2:
        connections = [
            "Concepts may have weak associative connections",
            "Could share very broad categorical relationships",
            "May be related through distant semantic paths",
            "Limited overlap in usage contexts"
        ]
    else:
        connections = [
            "Concepts appear to be largely unrelated",
            "May only share very abstract connections",
            "Limited semantic overlap detected",
            "Appear in distinct domains or categories"
        ]
    
    # Add concept-specific insights (basic heuristics)
    concept1_lower = concept1.lower()
    concept2_lower = concept2.lower()
    
    # Check for obvious relationships
    if concept1_lower in concept2_lower or concept2_lower in concept1_lower:
        connections.insert(0, "Concepts share textual components")
    
    # Add domain-specific insights
    if any(word in concept1_lower for word in ['dog', 'cat', 'bird', 'fish']) and \
       any(word in concept2_lower for word in ['dog', 'cat', 'bird', 'fish']):
        connections.insert(0, "Both concepts relate to animals")
    
    if any(word in concept1_lower for word in ['car', 'bike', 'train', 'plane']) and \
       any(word in concept2_lower for word in ['car', 'bike', 'train', 'plane']):
        connections.insert(0, "Both concepts relate to transportation")
    
    if any(word in concept1_lower for word in ['happy', 'sad', 'angry', 'joy']) and \
       any(word in concept2_lower for word in ['happy', 'sad', 'angry', 'joy']):
        connections.insert(0, "Both concepts relate to emotions")
    
    # Limit to 4 most relevant connections
    return connections[:4]


# Register the tool with FastMCP
mcp.tool(
    name="concept_relatedness",
    description="Calculate semantic relatedness score between two concepts using ConceptNet's embeddings",
    tags={"semantic", "relatedness", "comparison", "similarity"}
)(concept_relatedness)
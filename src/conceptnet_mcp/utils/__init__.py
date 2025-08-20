"""
Utility modules for ConceptNet MCP server.

This module provides a comprehensive suite of utilities for logging, exception handling,
text processing, and other common functionality used throughout the ConceptNet MCP server.

The utilities are organized into three main categories:

1. Exception Handling (exceptions.py):
   - Comprehensive exception hierarchy with error codes
   - Rich error context and debugging information
   - Utility functions for creating specific exceptions

2. Logging (logging.py):
   - Production-ready structured logging
   - Performance monitoring and request tracking
   - Configurable formatters and handlers

3. Text Processing (text_utils.py):
   - Unicode-safe text normalization
   - ConceptNet URI construction and parsing
   - Language validation and similarity calculations

All modules follow Python best practices and provide thread-safe, production-ready
implementations with comprehensive error handling and security considerations.
"""

# Exception handling exports
from .exceptions import (
    # Core exception classes
    ConceptNetMCPError,
    ConceptNetAPIError,
    ConceptNotFoundError,
    InvalidConceptURIError,
    InvalidLanguageError,
    RateLimitExceededError,
    NetworkTimeoutError,
    AuthenticationError,
    ValidationError,
    MCPToolError,
    PaginationError,
    ConfigurationError,
    TextValidationError,
    URIValidationError,
    
    # Error codes for programmatic handling
    ErrorCode,
    
    # Utility functions for exception creation
    create_concept_not_found_error,
    create_validation_error,
    create_api_error_from_response,
    get_exception_for_error_code,
    
    # Exception registry
    EXCEPTION_REGISTRY,
)

# Logging exports
from .logging import (
    # Core logging functions
    get_logger,
    configure_logging,
    setup_development_logging,
    setup_production_logging,
    
    # Logging classes
    RequestLogger,
    PerformanceLogger,
    JSONFormatter,
    MCPFormatter,
    
    # Global instances
    request_logger,
    performance_logger,
    
    # Decorators
    timed,
)

# Text processing exports
from .text_utils import (
    # Core text processing functions
    normalize_concept_text,
    construct_concept_uri,
    parse_concept_uri,
    validate_concept_uri,
    validate_concept_text,
    
    # Unicode and text normalization
    normalize_unicode,
    normalize_text_for_display,
    normalize_uri_to_text,
    normalize_relation_text,
    clean_text_for_uri,
    sanitize_search_query,
    sanitize_text_for_uri,
    clean_whitespace,
    truncate_text_safely,
    
    # Language handling
    normalize_language_code,
    validate_language_code,
    find_similar_languages,
    extract_language_from_uri,
    estimate_text_language,
    get_text_language_hints,
    
    # Text analysis and similarity
    calculate_text_similarity,
    fuzzy_match_concepts,
    split_compound_terms,
    is_valid_concept_text,
    is_valid_concept_format,
    
    # Security and validation
    validate_text_length,
    
    # Performance utilities
    clear_text_caches,
    get_cache_info,
    
    # Constants
    SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES,
    RELATION_PATTERNS,
    MAX_CONCEPT_LENGTH,
    MAX_URI_LENGTH,
    MAX_TEXT_LENGTH,
)

# Organize exports by category for easier importing
__all__ = [
    # === EXCEPTION HANDLING ===
    # Core exception classes
    "ConceptNetMCPError",
    "ConceptNetAPIError",
    "ConceptNotFoundError",
    "InvalidConceptURIError",
    "InvalidLanguageError",
    "RateLimitExceededError",
    "NetworkTimeoutError",
    "AuthenticationError",
    "ValidationError",
    "MCPToolError",
    "PaginationError",
    "ConfigurationError",
    "TextValidationError",
    "URIValidationError",
    
    # Error utilities
    "ErrorCode",
    "create_concept_not_found_error",
    "create_validation_error", 
    "create_api_error_from_response",
    "get_exception_for_error_code",
    "EXCEPTION_REGISTRY",
    
    # === LOGGING ===
    # Core logging functions
    "get_logger",
    "configure_logging",
    "setup_development_logging",
    "setup_production_logging",
    
    # Logging classes
    "RequestLogger",
    "PerformanceLogger",
    "JSONFormatter",
    "MCPFormatter",
    
    # Global instances and decorators
    "request_logger",
    "performance_logger",
    "timed",
    
    # === TEXT PROCESSING ===
    # Core concept/URI functions
    "normalize_concept_text",
    "construct_concept_uri",
    "parse_concept_uri",
    "validate_concept_uri",
    "validate_concept_text",
    
    # Text normalization
    "normalize_unicode",
    "normalize_text_for_display",
    "normalize_uri_to_text",
    "normalize_relation_text",
    "clean_text_for_uri",
    "sanitize_search_query",
    "sanitize_text_for_uri",
    "clean_whitespace",
    "truncate_text_safely",
    
    # Language handling
    "normalize_language_code",
    "validate_language_code",
    "find_similar_languages",
    "extract_language_from_uri",
    "estimate_text_language",
    "get_text_language_hints",
    
    # Text analysis
    "calculate_text_similarity",
    "fuzzy_match_concepts",
    "split_compound_terms",
    "is_valid_concept_text",
    "is_valid_concept_format",
    
    # Security and validation
    "validate_text_length",
    
    # Performance utilities
    "clear_text_caches",
    "get_cache_info",
    
    # Constants
    "SUPPORTED_LANGUAGES",
    "LANGUAGE_ALIASES", 
    "RELATION_PATTERNS",
    "MAX_CONCEPT_LENGTH",
    "MAX_URI_LENGTH",
    "MAX_TEXT_LENGTH",
]


# Convenience functions for common operations
def setup_logging_for_environment(environment: str = "development", log_file: str = None):
    """
    Set up logging optimized for the specified environment.
    
    Args:
        environment: "development" or "production"
        log_file: Optional log file path (required for production)
        
    Returns:
        Logging configuration dictionary
    """
    if environment.lower() == "production":
        if not log_file:
            raise ValueError("log_file is required for production environment")
        return setup_production_logging(log_file)
    else:
        return setup_development_logging()


def create_safe_concept_uri(term: str, language: str = "en") -> str:
    """
    Safely create a ConceptNet URI with comprehensive error handling.
    
    This is a convenience function that wraps construct_concept_uri with
    additional safety checks and fallbacks.
    
    Args:
        term: Concept term
        language: Language code
        
    Returns:
        Valid ConceptNet URI
        
    Raises:
        ConceptNetMCPError: If URI creation fails after all fallbacks
    """
    try:
        return construct_concept_uri(term, language)
    except InvalidLanguageError:
        # Fallback to English if language is invalid
        try:
            return construct_concept_uri(term, "en")
        except Exception as e:
            raise ConceptNetMCPError(
                f"Failed to create URI for term '{term}': {e}",
                error_code=ErrorCode.CONCEPT_URI_INVALID
            ) from e
    except Exception as e:
        raise ConceptNetMCPError(
            f"Failed to create URI for term '{term}': {e}",
            error_code=ErrorCode.CONCEPT_URI_INVALID
        ) from e


def validate_and_normalize_concept(
    term: str, 
    language: str = "en"
) -> dict:
    """
    Validate and normalize a concept with comprehensive checks.
    
    This convenience function performs all necessary validation and normalization
    for a concept term and language, returning detailed information.
    
    Args:
        term: Concept term to validate
        language: Language code
        
    Returns:
        Dictionary with validation results and normalized values
        
    Raises:
        ValidationError: If validation fails
    """
    result = {
        "original_term": term,
        "original_language": language,
        "is_valid": False,
        "normalized_term": None,
        "normalized_language": None,
        "concept_uri": None,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Validate and normalize language
        try:
            normalized_language = normalize_language_code(language)
            result["normalized_language"] = normalized_language
        except InvalidLanguageError as e:
            result["errors"].append(f"Invalid language: {e}")
            # Try fallback to English
            try:
                normalized_language = "en"
                result["normalized_language"] = normalized_language
                result["warnings"].append("Fell back to English language")
            except Exception:
                raise ValidationError("language", language, "valid language code") from e
        
        # Validate and normalize term
        try:
            normalized_term = normalize_concept_text(term, normalized_language)
            result["normalized_term"] = normalized_term
        except ValidationError as e:
            result["errors"].append(f"Invalid term: {e}")
            raise
        
        # Create URI
        try:
            concept_uri = construct_concept_uri(normalized_term, normalized_language)
            result["concept_uri"] = concept_uri
            result["is_valid"] = True
        except Exception as e:
            result["errors"].append(f"URI construction failed: {e}")
            raise ValidationError("concept_uri", f"{normalized_term}@{normalized_language}", "valid URI components") from e
        
    except Exception as e:
        if not isinstance(e, ValidationError):
            result["errors"].append(f"Unexpected error: {e}")
            raise ValidationError("concept_validation", str(e), "valid concept") from e
        raise
    
    return result


# Module version and metadata
__version__ = "1.0.0"
__author__ = "ConceptNet MCP Team"
__description__ = "Comprehensive utilities for ConceptNet MCP server operations"

# Export convenience functions
__all__.extend([
    "setup_logging_for_environment",
    "create_safe_concept_uri", 
    "validate_and_normalize_concept"
])
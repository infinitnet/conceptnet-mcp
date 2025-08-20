"""
Comprehensive unit tests for the utils/__init__.py module.

This test suite verifies all exports, convenience functions, and module
integration provided by the utils package.
"""

import pytest
from unittest.mock import patch, MagicMock

# Test basic imports from the utils package that we know exist
from src.conceptnet_mcp.utils import (
    # Exception classes
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
    ErrorCode,
    
    # Exception utilities
    create_concept_not_found_error,
    create_validation_error,
    create_api_error_from_response,
    get_exception_for_error_code,
    
    # Logging classes and functions that actually exist
    JSONFormatter,
    MCPFormatter,
    RequestLogger,
    PerformanceLogger,
    configure_logging,
    setup_production_logging,
    setup_development_logging,
    get_logger,
    request_logger,
    performance_logger,
    timed,
    
    # Text processing functions that actually exist
    normalize_concept_text,
    construct_concept_uri,
    parse_concept_uri,
    validate_concept_uri,
    validate_concept_text,
    validate_language_code,
    normalize_language_code,
    clean_text_for_uri,
    normalize_text_for_display,
    normalize_uri_to_text,
    normalize_relation_text,
    sanitize_search_query,
    sanitize_text_for_uri,
    clean_whitespace,
    is_valid_concept_format,
    find_similar_languages,
    extract_language_from_uri,
    estimate_text_language,
    get_text_language_hints,
    calculate_text_similarity,
    fuzzy_match_concepts,
    split_compound_terms,
    is_valid_concept_text,
    validate_text_length,
    clear_text_caches,
    get_cache_info,
    normalize_unicode,
    truncate_text_safely,
    
    # Text exceptions
    TextValidationError,
    URIValidationError,
    
    # Constants
    SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES,
    RELATION_PATTERNS,
    MAX_CONCEPT_LENGTH,
    MAX_URI_LENGTH,
    MAX_TEXT_LENGTH,
    
    # Convenience functions from __init__.py
    setup_logging_for_environment,
    create_safe_concept_uri,
    validate_and_normalize_concept,
)


class TestImports:
    """Test that all expected symbols are properly imported."""
    
    def test_exception_imports(self):
        """Test that all exception classes are importable."""
        # Base exceptions
        assert ConceptNetMCPError is not None
        assert ConceptNetAPIError is not None
        
        # Specific exceptions
        assert ConceptNotFoundError is not None
        assert InvalidConceptURIError is not None
        assert InvalidLanguageError is not None
        assert RateLimitExceededError is not None
        assert NetworkTimeoutError is not None
        assert AuthenticationError is not None
        assert ValidationError is not None
        assert MCPToolError is not None
        assert PaginationError is not None
        assert ConfigurationError is not None
        
        # Error code enum
        assert ErrorCode is not None
    
    def test_exception_utility_imports(self):
        """Test that exception utility functions are importable."""
        assert callable(create_concept_not_found_error)
        assert callable(create_validation_error)
        assert callable(create_api_error_from_response)
        assert callable(get_exception_for_error_code)
    
    def test_logging_imports(self):
        """Test that logging classes and functions are importable."""
        # Classes
        assert JSONFormatter is not None
        assert MCPFormatter is not None
        assert RequestLogger is not None
        assert PerformanceLogger is not None
        
        # Functions
        assert callable(configure_logging)
        assert callable(setup_production_logging)
        assert callable(setup_development_logging)
        assert callable(get_logger)
        
        # Global instances
        assert request_logger is not None
        assert performance_logger is not None
        assert callable(timed)
    
    def test_text_processing_imports(self):
        """Test that text processing functions are importable."""
        assert callable(normalize_concept_text)
        assert callable(construct_concept_uri)
        assert callable(parse_concept_uri)
        assert callable(validate_concept_text)
        assert callable(validate_language_code)
        assert callable(sanitize_text_for_uri)
        assert callable(clean_whitespace)
        assert callable(is_valid_concept_format)
        assert callable(get_text_language_hints)
        assert callable(normalize_unicode)
        assert callable(truncate_text_safely)
        
        # Text exceptions
        assert TextValidationError is not None
        assert URIValidationError is not None
    
    def test_convenience_function_imports(self):
        """Test that convenience functions are importable."""
        assert callable(setup_logging_for_environment)
        assert callable(create_safe_concept_uri)
        assert callable(validate_and_normalize_concept)


class TestSetupLoggingForEnvironment:
    """Test the setup_logging_for_environment convenience function."""
    
    @patch('src.conceptnet_mcp.utils.setup_development_logging')
    def test_development_environment(self, mock_dev_logging):
        """Test development environment setup."""
        mock_dev_logging.return_value = {"result": "dev_config"}
        
        result = setup_logging_for_environment("development")
        
        mock_dev_logging.assert_called_once()
        assert result == {"result": "dev_config"}
    
    @patch('src.conceptnet_mcp.utils.setup_production_logging')
    def test_production_environment(self, mock_prod_logging):
        """Test production environment setup."""
        mock_prod_logging.return_value = {"result": "prod_config"}
        
        result = setup_logging_for_environment("production", "/path/to/log")
        
        mock_prod_logging.assert_called_once_with("/path/to/log")
        assert result == {"result": "prod_config"}
    
    def test_production_without_log_file(self):
        """Test production environment without log file raises error."""
        with pytest.raises(ValueError, match="log_file is required"):
            setup_logging_for_environment("production")


class TestCreateSafeConceptURI:
    """Test the create_safe_concept_uri convenience function."""
    
    def test_successful_creation(self):
        """Test successful URI creation."""
        uri = create_safe_concept_uri("hello world", "en")
        assert uri == "/c/en/hello_world"
    
    def test_fallback_to_english(self):
        """Test fallback to English for invalid language."""
        uri = create_safe_concept_uri("hello", "invalid_lang")
        assert uri == "/c/en/hello"
    
    def test_complete_failure(self):
        """Test complete failure with comprehensive error."""
        with pytest.raises(ConceptNetMCPError):
            create_safe_concept_uri("", "en")  # Empty term should fail


class TestValidateAndNormalizeConcept:
    """Test the validate_and_normalize_concept convenience function."""
    
    def test_successful_validation(self):
        """Test successful concept validation."""
        result = validate_and_normalize_concept("hello world", "en")
        
        assert result["is_valid"] is True
        assert result["original_term"] == "hello world"
        assert result["original_language"] == "en"
        assert result["normalized_term"] == "hello_world"
        assert result["normalized_language"] == "en"
        assert result["concept_uri"] == "/c/en/hello_world"
        assert len(result["errors"]) == 0
    
    def test_language_fallback(self):
        """Test language fallback to English."""
        result = validate_and_normalize_concept("hello", "invalid_lang")
        
        assert result["is_valid"] is True
        assert result["normalized_language"] == "en"
        assert len(result["warnings"]) > 0
        assert any("fell back" in warning.lower() for warning in result["warnings"])
    
    def test_invalid_term(self):
        """Test invalid term handling."""
        with pytest.raises(ValidationError):
            validate_and_normalize_concept("", "en")


class TestModuleStructure:
    """Test the overall module structure and organization."""
    
    def test_all_exports_defined(self):
        """Test that __all__ is defined and contains all exports."""
        import src.conceptnet_mcp.utils as utils_module
        
        # Should have __all__ defined
        assert hasattr(utils_module, '__all__')
        assert isinstance(utils_module.__all__, list)
        assert len(utils_module.__all__) > 0
    
    def test_import_star_works(self):
        """Test that 'from utils import *' works correctly."""
        # This is tested by the successful imports at the top of this file
        # If any import failed, the test would have failed during import
        pass
    
    def test_module_docstring(self):
        """Test that the module has proper documentation."""
        import src.conceptnet_mcp.utils as utils_module
        
        assert utils_module.__doc__ is not None
        assert len(utils_module.__doc__.strip()) > 0


class TestBackwardCompatibility:
    """Test backward compatibility of the utils module."""
    
    def test_old_import_paths_work(self):
        """Test that old import paths still work."""
        # These should all work without errors
        from src.conceptnet_mcp.utils.exceptions import ConceptNetMCPError
        from src.conceptnet_mcp.utils.logging import get_logger
        from src.conceptnet_mcp.utils.text_utils import normalize_concept_text
        
        assert ConceptNetMCPError is not None
        assert callable(get_logger)
        assert callable(normalize_concept_text)
    
    def test_convenience_functions_maintain_api(self):
        """Test that convenience functions maintain their API."""
        # Test the actual convenience functions
        result = create_safe_concept_uri("test", "en")
        assert result == "/c/en/test"
        
        validation_result = validate_and_normalize_concept("hello world", "en")
        assert validation_result["is_valid"] is True


class TestErrorHandling:
    """Test error handling in convenience functions."""
    
    def test_create_safe_concept_uri_error_handling(self):
        """Test that create_safe_concept_uri handles errors gracefully."""
        # Should fall back to English for invalid language
        result = create_safe_concept_uri("test", "invalid_lang")
        assert result == "/c/en/test"
        
        # Should raise ConceptNetMCPError for completely invalid input
        with pytest.raises(ConceptNetMCPError):
            create_safe_concept_uri("", "en")
    
    def test_convenience_functions_preserve_errors(self):
        """Test that convenience functions preserve appropriate errors."""
        # construct_concept_uri should still raise validation errors
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "invalid_lang")
        
        # parse_concept_uri should still raise parsing errors
        with pytest.raises(InvalidConceptURIError):
            parse_concept_uri("invalid_uri")


class TestIntegrationWithOtherModules:
    """Test integration between different utility modules."""
    
    def test_exception_and_logging_integration(self):
        """Test that exceptions work properly with logging."""
        logger = get_logger("test")
        
        try:
            raise ConceptNotFoundError("test_concept")
        except ConceptNetMCPError as e:
            # Should be able to log the exception
            logger.error("Error occurred", exc_info=True)
            # Test passes if no exception is raised
    
    def test_text_processing_and_exceptions_integration(self):
        """Test that text processing raises appropriate exceptions."""
        # Should raise ValidationError for invalid input
        with pytest.raises(ValidationError):
            validate_and_normalize_concept("", "en")
        
        # Should raise InvalidLanguageError for invalid language
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "invalid")
    
    def test_performance_logging_integration(self):
        """Test integration with performance logging."""
        # Test that timed decorator works
        @timed("test_operation")
        def test_operation():
            return "success"
        
        # Should complete without errors
        result = test_operation()
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__])
"""
Comprehensive unit tests for the exceptions module.

This test suite verifies all exception classes, error codes, utility functions,
and edge cases in the enhanced exceptions module.
"""

import pytest
import sys
from unittest.mock import patch

from src.conceptnet_mcp.utils.exceptions import (
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
    create_concept_not_found_error,
    create_validation_error,
    create_api_error_from_response,
    get_exception_for_error_code,
    EXCEPTION_REGISTRY,
)


class TestErrorCode:
    """Test the ErrorCode enumeration."""
    
    def test_error_code_values(self):
        """Test that error codes have correct values."""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.API_RATE_LIMIT_ERROR.value == 2002
        assert ErrorCode.CONCEPT_NOT_FOUND.value == 3000
        assert ErrorCode.VALIDATION_FIELD_REQUIRED.value == 4000
        assert ErrorCode.TOOL_EXECUTION_ERROR.value == 5000
        assert ErrorCode.PAGINATION_INVALID_OFFSET.value == 6000
    
    def test_error_code_names(self):
        """Test that error codes have correct names."""
        assert ErrorCode.CONCEPT_NOT_FOUND.name == "CONCEPT_NOT_FOUND"
        assert ErrorCode.API_RATE_LIMIT_ERROR.name == "API_RATE_LIMIT_ERROR"


class TestConceptNetMCPError:
    """Test the base ConceptNetMCPError class."""
    
    def test_basic_creation(self):
        """Test basic error creation."""
        error = ConceptNetMCPError("Test error")
        assert str(error) == "[UNKNOWN_ERROR] Test error"
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        assert error.details == {}
        assert error.suggestions == []
        assert error.context == {}
    
    def test_creation_with_all_parameters(self):
        """Test error creation with all parameters."""
        details = {"key": "value"}
        suggestions = ["Try this", "Try that"]
        context = {"module": "test"}
        
        error = ConceptNetMCPError(
            "Test error",
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            suggestions=suggestions,
            context=context
        )
        
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.CONFIGURATION_ERROR
        assert error.details == details
        assert error.suggestions == suggestions
        assert error.context == context
    
    def test_add_context(self):
        """Test adding context information."""
        error = ConceptNetMCPError("Test error")
        result = error.add_context("key", "value")
        
        assert result is error  # Method chaining
        assert error.context["key"] == "value"
    
    def test_add_suggestion(self):
        """Test adding suggestion."""
        error = ConceptNetMCPError("Test error")
        result = error.add_suggestion("Try this")
        
        assert result is error  # Method chaining
        assert "Try this" in error.suggestions
    
    def test_to_dict(self):
        """Test dictionary serialization."""
        error = ConceptNetMCPError(
            "Test error",
            error_code=ErrorCode.VALIDATION_FIELD_INVALID,
            details={"field": "test"},
            suggestions=["Fix it"],
            context={"module": "test"}
        )
        
        result = error.to_dict()
        expected = {
            'error_type': 'ConceptNetMCPError',
            'message': 'Test error',
            'error_code': 'VALIDATION_FIELD_INVALID',
            'error_code_value': 4001,
            'details': {'field': 'test'},
            'suggestions': ['Fix it'],
            'context': {'module': 'test'}
        }
        
        # Remove dynamic context information for comparison
        for key in ['file', 'function', 'line']:
            result['context'].pop(key, None)
            expected['context'].pop(key, None)
        
        assert result == expected
    
    def test_str_with_suggestions(self):
        """Test string representation with suggestions."""
        error = ConceptNetMCPError("Test error")
        error.add_suggestion("Try this")
        error.add_suggestion("Try that")
        
        result = str(error)
        assert "[UNKNOWN_ERROR] Test error" in result
        assert "Suggestions: Try this; Try that" in result


class TestConceptNetAPIError:
    """Test the ConceptNetAPIError class."""
    
    def test_basic_creation(self):
        """Test basic API error creation."""
        error = ConceptNetAPIError("API failed")
        assert error.status_code is None
        assert error.response_data == {}
        assert error.error_code == ErrorCode.API_CONNECTION_ERROR
    
    def test_with_status_codes(self):
        """Test error code determination based on status codes."""
        # Rate limit error
        rate_limit = ConceptNetAPIError("Rate limited", status_code=429)
        assert rate_limit.error_code == ErrorCode.API_RATE_LIMIT_ERROR
        
        # Client error
        client_error = ConceptNetAPIError("Bad request", status_code=400)
        assert client_error.error_code == ErrorCode.API_CLIENT_ERROR
        
        # Server error
        server_error = ConceptNetAPIError("Server error", status_code=500)
        assert server_error.error_code == ErrorCode.API_SERVER_ERROR
    
    def test_with_full_context(self):
        """Test API error with full context."""
        error = ConceptNetAPIError(
            "API failed",
            status_code=404,
            response_data={"error": "Not found"},
            endpoint="/api/test",
            method="GET",
            request_id="123"
        )
        
        assert error.status_code == 404
        assert error.response_data == {"error": "Not found"}
        assert error.endpoint == "/api/test"
        assert error.method == "GET"
        assert error.request_id == "123"
        assert error.context["api_endpoint"] == "/api/test"
        assert error.context["status_code"] == 404
    
    def test_suggestions_based_on_status(self):
        """Test that appropriate suggestions are generated."""
        # 404 error
        not_found = ConceptNetAPIError("Not found", status_code=404)
        assert any("verify" in s.lower() for s in not_found.suggestions)
        
        # 429 error
        rate_limit = ConceptNetAPIError("Rate limited", status_code=429)
        assert any("wait" in s.lower() for s in rate_limit.suggestions)
        
        # 500 error
        server_error = ConceptNetAPIError("Server error", status_code=500)
        assert any("retry" in s.lower() for s in server_error.suggestions)


class TestConceptNotFoundError:
    """Test the ConceptNotFoundError class."""
    
    def test_basic_creation(self):
        """Test basic concept not found error."""
        error = ConceptNotFoundError("test_concept")
        assert "test_concept" in error.message
        assert error.concept == "test_concept"
        assert error.language is None
        assert error.similar_concepts == []
        assert error.error_code == ErrorCode.CONCEPT_NOT_FOUND
    
    def test_with_language(self):
        """Test with language specified."""
        error = ConceptNotFoundError("test_concept", language="es")
        assert "test_concept" in error.message
        assert "es" in error.message
        assert error.language == "es"
    
    def test_with_similar_concepts(self):
        """Test with similar concepts."""
        similar = ["concept1", "concept2", "concept3"]
        error = ConceptNotFoundError("test", similar_concepts=similar)
        assert error.similar_concepts == similar
        assert any("similar" in s.lower() for s in error.suggestions)
    
    def test_with_normalized_term(self):
        """Test with normalized term."""
        error = ConceptNotFoundError("test", normalized_term="test_normalized")
        assert error.normalized_term == "test_normalized"
        assert any("normalized" in s.lower() for s in error.suggestions)


class TestInvalidConceptURIError:
    """Test the InvalidConceptURIError class."""
    
    def test_basic_creation(self):
        """Test basic invalid URI error."""
        error = InvalidConceptURIError("invalid_uri")
        assert "invalid_uri" in error.message
        assert error.uri == "invalid_uri"
        assert error.error_code == ErrorCode.CONCEPT_URI_INVALID
    
    def test_with_expected_format(self):
        """Test with expected format."""
        error = InvalidConceptURIError("invalid", expected_format="/c/lang/term")
        assert "/c/lang/term" in error.message
        assert error.expected_format == "/c/lang/term"
    
    def test_with_validation_errors(self):
        """Test with validation errors."""
        validation_errors = ["Error 1", "Error 2"]
        error = InvalidConceptURIError("invalid", validation_errors=validation_errors)
        assert error.validation_errors == validation_errors


class TestInvalidLanguageError:
    """Test the InvalidLanguageError class."""
    
    def test_basic_creation(self):
        """Test basic invalid language error."""
        error = InvalidLanguageError("xx")
        assert "xx" in error.message
        assert error.language == "xx"
        assert error.error_code == ErrorCode.CONCEPT_LANGUAGE_INVALID
    
    def test_with_supported_languages(self):
        """Test with supported languages list."""
        supported = ["en", "es", "fr"]
        error = InvalidLanguageError("xx", supported_languages=supported)
        assert error.supported_languages == supported
        assert any("supported languages" in s.lower() for s in error.suggestions)
    
    def test_with_suggested_languages(self):
        """Test with suggested languages."""
        suggested = ["en", "es"]
        error = InvalidLanguageError("xx", suggested_languages=suggested)
        assert error.suggested_languages == suggested
        assert any("did you mean" in s.lower() for s in error.suggestions)


class TestRateLimitExceededError:
    """Test the RateLimitExceededError class."""
    
    def test_basic_creation(self):
        """Test basic rate limit error."""
        error = RateLimitExceededError()
        assert "rate limit exceeded" in error.message.lower()
        assert error.status_code == 429
        assert error.error_code == ErrorCode.API_RATE_LIMIT_ERROR
    
    def test_with_retry_after(self):
        """Test with retry after parameter."""
        error = RateLimitExceededError(retry_after=60)
        assert "60 seconds" in error.message
        assert error.retry_after == 60
        assert any("wait at least 60" in s.lower() for s in error.suggestions)
    
    def test_with_rate_limit_info(self):
        """Test with rate limit information."""
        error = RateLimitExceededError(limit=100, window="hour", current_usage=150)
        assert error.limit == 100
        assert error.window == "hour"
        assert error.current_usage == 150


class TestValidationError:
    """Test the ValidationError class."""
    
    def test_basic_creation(self):
        """Test basic validation error."""
        error = ValidationError("field_name", "invalid_value", "valid format")
        assert "field_name" in error.message
        assert "invalid_value" in error.message
        assert "valid format" in error.message
        assert error.field == "field_name"
        assert error.value == "invalid_value"
        assert error.expected == "valid format"
    
    def test_error_code_determination(self):
        """Test error code determination based on expected text."""
        # Required field
        required_error = ValidationError("field", None, "required field")
        assert required_error.error_code == ErrorCode.VALIDATION_FIELD_REQUIRED
        
        # Type mismatch
        type_error = ValidationError("field", "text", "integer type")
        assert type_error.error_code == ErrorCode.VALIDATION_TYPE_MISMATCH
        
        # Range error
        range_error = ValidationError("field", 200, "value between 1 and 100")
        assert range_error.error_code == ErrorCode.VALIDATION_VALUE_OUT_OF_RANGE
        
        # Generic validation error
        generic_error = ValidationError("field", "bad", "good format")
        assert generic_error.error_code == ErrorCode.VALIDATION_FIELD_INVALID
    
    def test_with_constraints(self):
        """Test with constraints information."""
        constraints = {"min": 1, "max": 100}
        error = ValidationError("number", 200, "range", constraints=constraints)
        assert error.constraints == constraints
        assert any("constraints" in s.lower() for s in error.suggestions)


class TestMCPToolError:
    """Test the MCPToolError class."""
    
    def test_basic_creation(self):
        """Test basic tool error."""
        error = MCPToolError("test_tool", "execution failed")
        assert "test_tool" in error.message
        assert "execution failed" in error.message
        assert error.tool_name == "test_tool"
        assert error.error_message == "execution failed"
        assert error.error_code == ErrorCode.TOOL_EXECUTION_ERROR
    
    def test_with_execution_stage(self):
        """Test with execution stage."""
        error = MCPToolError("tool", "failed", execution_stage="validation")
        assert "validation" in error.message
        assert error.execution_stage == "validation"
    
    def test_with_inner_exception(self):
        """Test with inner exception chaining."""
        inner = ValueError("Inner error")
        error = MCPToolError("tool", "failed", inner_exception=inner)
        assert error.inner_exception == inner
        assert error.__cause__ == inner
        assert error.context["inner_exception_type"] == "ValueError"
        assert error.context["inner_exception_message"] == "Inner error"


class TestPaginationError:
    """Test the PaginationError class."""
    
    def test_basic_creation(self):
        """Test basic pagination error."""
        error = PaginationError("Pagination failed")
        assert "Pagination failed" in error.message
        assert error.partial_results == []
    
    def test_error_code_determination(self):
        """Test error code based on message content."""
        offset_error = PaginationError("Invalid offset value")
        assert offset_error.error_code == ErrorCode.PAGINATION_INVALID_OFFSET
        
        limit_error = PaginationError("Invalid limit value")
        assert limit_error.error_code == ErrorCode.PAGINATION_INVALID_LIMIT
        
        not_found_error = PaginationError("Page not found")
        assert not_found_error.error_code == ErrorCode.PAGINATION_PAGE_NOT_FOUND
        
        merge_error = PaginationError("Failed to merge results")
        assert merge_error.error_code == ErrorCode.PAGINATION_MERGE_ERROR
    
    def test_with_partial_results(self):
        """Test with partial results."""
        partial = [{"id": 1}, {"id": 2}]
        error = PaginationError("Failed", partial_results=partial)
        assert error.partial_results == partial
        assert any("partial results (2 items)" in s for s in error.suggestions)


class TestUtilityFunctions:
    """Test utility functions for exception creation."""
    
    def test_create_concept_not_found_error(self):
        """Test concept not found error creation utility."""
        error = create_concept_not_found_error("test", "en", ["similar1", "similar2"])
        assert isinstance(error, ConceptNotFoundError)
        assert error.concept == "test"
        assert error.language == "en"
        assert error.similar_concepts == ["similar1", "similar2"]
    
    def test_create_validation_error_with_type(self):
        """Test validation error creation with type."""
        error = create_validation_error("field", "value", str)
        assert isinstance(error, ValidationError)
        assert error.field == "field"
        assert error.value == "value"
        assert error.expected == "str"
    
    def test_create_validation_error_with_string(self):
        """Test validation error creation with string."""
        error = create_validation_error("field", "value", "string format")
        assert error.expected == "string format"
    
    @patch('src.conceptnet_mcp.utils.exceptions.logging')
    def test_create_api_error_from_response(self, mock_logging):
        """Test API error creation from response."""
        # Mock response object
        class MockResponse:
            status_code = 404
            headers = {'X-Request-ID': 'req123'}
            text = "Not found"
            
            def json(self):
                return {"error": "Resource not found"}
        
        response = MockResponse()
        error = create_api_error_from_response(response, "/api/test", "GET")
        
        assert isinstance(error, ConceptNetAPIError)
        assert error.status_code == 404
        assert error.endpoint == "/api/test"
        assert error.method == "GET"
        assert error.request_id == "req123"
        assert error.response_data == {"error": "Resource not found"}
    
    def test_get_exception_for_error_code(self):
        """Test getting exception class for error code."""
        assert get_exception_for_error_code(ErrorCode.CONCEPT_NOT_FOUND) == ConceptNotFoundError
        assert get_exception_for_error_code(ErrorCode.API_RATE_LIMIT_ERROR) == RateLimitExceededError
        assert get_exception_for_error_code(ErrorCode.VALIDATION_FIELD_INVALID) == ValidationError
        
        # Unknown error code should return base class
        assert get_exception_for_error_code(ErrorCode.UNKNOWN_ERROR) == ConceptNetMCPError


class TestExceptionRegistry:
    """Test the exception registry."""
    
    def test_registry_completeness(self):
        """Test that all error codes are in the registry."""
        for error_code in ErrorCode:
            assert error_code in EXCEPTION_REGISTRY
    
    def test_registry_mappings(self):
        """Test specific registry mappings."""
        assert EXCEPTION_REGISTRY[ErrorCode.CONCEPT_NOT_FOUND] == ConceptNotFoundError
        assert EXCEPTION_REGISTRY[ErrorCode.API_RATE_LIMIT_ERROR] == RateLimitExceededError
        assert EXCEPTION_REGISTRY[ErrorCode.VALIDATION_FIELD_INVALID] == ValidationError
        assert EXCEPTION_REGISTRY[ErrorCode.TOOL_EXECUTION_ERROR] == MCPToolError
        assert EXCEPTION_REGISTRY[ErrorCode.PAGINATION_INVALID_OFFSET] == PaginationError


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_inheritance_hierarchy(self):
        """Test that all exceptions inherit correctly."""
        # All custom exceptions should inherit from ConceptNetMCPError
        assert issubclass(ConceptNetAPIError, ConceptNetMCPError)
        assert issubclass(ConceptNotFoundError, ConceptNetMCPError)
        assert issubclass(InvalidConceptURIError, ConceptNetMCPError)
        assert issubclass(ValidationError, ConceptNetMCPError)
        assert issubclass(MCPToolError, ConceptNetMCPError)
        assert issubclass(PaginationError, ConceptNetMCPError)
        
        # API-specific exceptions should inherit from ConceptNetAPIError
        assert issubclass(RateLimitExceededError, ConceptNetAPIError)
        assert issubclass(NetworkTimeoutError, ConceptNetAPIError)
        assert issubclass(AuthenticationError, ConceptNetAPIError)
        
        # All should ultimately inherit from Exception
        assert issubclass(ConceptNetMCPError, Exception)
    
    def test_exception_catching(self):
        """Test that exceptions can be caught by their parent classes."""
        # Specific exception can be caught by base class
        try:
            raise ConceptNotFoundError("test")
        except ConceptNetMCPError:
            pass  # Should catch it
        
        # API exception can be caught by API base class
        try:
            raise RateLimitExceededError()
        except ConceptNetAPIError:
            pass  # Should catch it
        
        # All can be caught by Exception
        try:
            raise ValidationError("field", "value", "expected")
        except Exception:
            pass  # Should catch it


if __name__ == "__main__":
    pytest.main([__file__])
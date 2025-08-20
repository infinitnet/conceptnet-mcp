"""
Custom exception classes for ConceptNet MCP server.

This module defines a comprehensive hierarchy of custom exception classes for handling
various error conditions that can occur during ConceptNet API interactions and MCP operations.

The exception hierarchy follows Python best practices:
- All custom exceptions inherit from Exception (not BaseException)
- Proper exception chaining is used where appropriate
- Rich context information is provided for debugging
- Error codes support programmatic error handling
- Meaningful error messages guide users toward solutions

Exception Hierarchy:
    ConceptNetMCPError (base)
    ├── ConceptNetAPIError (API-related errors)
    │   ├── RateLimitExceededError
    │   ├── NetworkTimeoutError
    │   └── AuthenticationError
    ├── ConceptNotFoundError (concept lookup failures)
    ├── InvalidConceptURIError (URI format errors)
    ├── InvalidLanguageError (language validation errors)
    ├── ValidationError (data validation failures)
    ├── MCPToolError (tool execution errors)
    ├── PaginationError (pagination handling errors)
    └── ConfigurationError (server configuration errors)
"""

import sys
import logging
from typing import Any, Optional, Dict, List, Union
from enum import Enum


class ErrorCode(Enum):
    """
    Enumeration of error codes for programmatic error handling.
    
    Error codes follow a structured format: CATEGORY_SPECIFIC_ERROR
    This allows for easy categorization and handling of different error types.
    """
    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    CONFIGURATION_ERROR = 1001
    INTERNAL_ERROR = 1002
    
    # ConceptNet API errors (2000-2999)
    API_CONNECTION_ERROR = 2000
    API_TIMEOUT_ERROR = 2001
    API_RATE_LIMIT_ERROR = 2002
    API_AUTHENTICATION_ERROR = 2003
    API_SERVER_ERROR = 2004
    API_CLIENT_ERROR = 2005
    
    # Concept errors (3000-3999)
    CONCEPT_NOT_FOUND = 3000
    CONCEPT_URI_INVALID = 3001
    CONCEPT_LANGUAGE_INVALID = 3002
    CONCEPT_TERM_INVALID = 3003
    
    # Validation errors (4000-4999)
    VALIDATION_FIELD_REQUIRED = 4000
    VALIDATION_FIELD_INVALID = 4001
    VALIDATION_TYPE_MISMATCH = 4002
    VALIDATION_VALUE_OUT_OF_RANGE = 4003
    
    # MCP Tool errors (5000-5999)
    TOOL_EXECUTION_ERROR = 5000
    TOOL_PARAMETER_ERROR = 5001
    TOOL_TIMEOUT_ERROR = 5002
    
    # Pagination errors (6000-6999)
    PAGINATION_INVALID_OFFSET = 6000
    PAGINATION_INVALID_LIMIT = 6001
    PAGINATION_PAGE_NOT_FOUND = 6002
    PAGINATION_MERGE_ERROR = 6003
    
    # Text processing errors (7000-7999)
    TEXT_VALIDATION_ERROR = 7000
    URI_VALIDATION_ERROR = 7001


class ConceptNetMCPError(Exception):
    """
    Base exception class for ConceptNet MCP server errors.
    
    This is the root exception class from which all other ConceptNet MCP specific
    exceptions inherit. It provides a rich error context including error codes,
    suggestions for resolution, and detailed debugging information.
    
    Attributes:
        message: Human-readable error message
        error_code: Structured error code for programmatic handling
        details: Additional context information for debugging
        suggestions: List of suggested actions to resolve the error
        context: Contextual information about when/where the error occurred
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        add_frame_info: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.suggestions = suggestions or []
        self.context = context or {}
        
        # Add exception chaining information if requested
        if add_frame_info and hasattr(sys, '_getframe'):
            try:
                frame = sys._getframe(1)
                self.context.update({
                    'file': frame.f_code.co_filename,
                    'function': frame.f_code.co_name,
                    'line': frame.f_lineno
                })
            except (AttributeError, ValueError):
                # _getframe not available or failed
                pass
    
    def add_context(self, key: str, value: Any) -> 'ConceptNetMCPError':
        """
        Add additional context information to the exception.
        
        Args:
            key: Context key
            value: Context value
            
        Returns:
            Self for method chaining
        """
        self.context[key] = value
        return self
    
    def add_suggestion(self, suggestion: str) -> 'ConceptNetMCPError':
        """
        Add a suggestion for resolving the error.
        
        Args:
            suggestion: Human-readable suggestion
            
        Returns:
            Self for method chaining
        """
        self.suggestions.append(suggestion)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code.name,
            'error_code_value': self.error_code.value,
            'details': self.details,
            'suggestions': self.suggestions,
            'context': self.context
        }
    
    def __str__(self) -> str:
        """Enhanced string representation with error code and suggestions."""
        result = f"[{self.error_code.name}] {self.message}"
        if self.suggestions:
            result += f"\nSuggestions: {'; '.join(self.suggestions)}"
        return result
    
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        message: Optional[str] = None,
        error_code: Optional[ErrorCode] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> 'ConceptNetMCPError':
        """
        Create a ConceptNetMCPError from an existing exception.
        
        This method provides exception chaining functionality, allowing you to
        wrap existing exceptions while preserving their information and adding
        ConceptNet-specific context.
        
        Args:
            exception: The original exception to wrap
            message: Custom message (uses original exception message if None)
            error_code: Specific error code (uses UNKNOWN_ERROR if None)
            additional_context: Additional context to add
            
        Returns:
            New ConceptNetMCPError instance that wraps the original exception
        """
        if message is None:
            message = str(exception)
        
        if error_code is None:
            error_code = ErrorCode.UNKNOWN_ERROR
        
        # Create new exception with chaining
        new_exception = cls(
            message=message,
            error_code=error_code,
            context=additional_context or {}
        )
        
        # Set up exception chaining
        new_exception.__cause__ = exception
        
        # Add information about the original exception
        new_exception.add_context('original_exception_type', type(exception).__name__)
        new_exception.add_context('original_exception_message', str(exception))
        
        # Add traceback information if available
        if hasattr(exception, '__traceback__') and exception.__traceback__:
            import traceback
            tb_lines = traceback.format_tb(exception.__traceback__)
            new_exception.add_context('original_traceback', tb_lines[-3:])  # Last 3 frames
        
        return new_exception


class ConceptNetAPIError(ConceptNetMCPError):
    """
    Exception raised when ConceptNet API returns an error.
    
    This exception is raised for HTTP errors, API timeouts, network issues,
    and other ConceptNet service-related problems. It provides detailed
    information about the API response and suggested recovery actions.
    
    Attributes:
        status_code: HTTP status code from the API response
        response_data: Raw response data from the API
        endpoint: The API endpoint that was called
        method: HTTP method used (GET, POST, etc.)
        request_id: Unique identifier for the request (if available)
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        # Determine appropriate error code based on status code
        if status_code == 429:
            error_code = ErrorCode.API_RATE_LIMIT_ERROR
        elif status_code and 400 <= status_code < 500:
            error_code = ErrorCode.API_CLIENT_ERROR
        elif status_code and 500 <= status_code < 600:
            error_code = ErrorCode.API_SERVER_ERROR
        else:
            error_code = ErrorCode.API_CONNECTION_ERROR
        
        # Generate helpful suggestions based on error type
        suggestions = []
        if status_code == 429:
            suggestions.append("Wait before retrying the request")
            suggestions.append("Implement exponential backoff in your retry logic")
        elif status_code and 500 <= status_code < 600:
            suggestions.append("Retry the request after a short delay")
            suggestions.append("Check ConceptNet service status")
        elif status_code == 404:
            suggestions.append("Verify the concept or endpoint exists")
            suggestions.append("Check the URI format and spelling")
        
        super().__init__(
            message=message,
            error_code=error_code,
            suggestions=suggestions
        )
        
        self.status_code = status_code
        self.response_data = response_data or {}
        self.endpoint = endpoint
        self.method = method
        self.request_id = request_id
        
        # Add API-specific context
        self.add_context('api_endpoint', endpoint)
        self.add_context('http_method', method)
        self.add_context('status_code', status_code)
        self.add_context('request_id', request_id)


class ConceptNotFoundError(ConceptNetMCPError):
    """
    Exception raised when a requested concept is not found in ConceptNet.
    
    This exception is raised when a concept URI or term does not exist
    in the ConceptNet knowledge base. It provides helpful suggestions
    for alternative concepts and troubleshooting steps.
    
    Attributes:
        concept: The concept term or URI that was not found
        language: The language code used in the search
        similar_concepts: List of similar concepts that were found
        normalized_term: The normalized version of the concept term
    """
    
    def __init__(
        self,
        concept: str,
        language: Optional[str] = None,
        similar_concepts: Optional[List[str]] = None,
        normalized_term: Optional[str] = None
    ):
        message = f"Concept not found: '{concept}'"
        if language:
            message += f" (language: {language})"
        
        suggestions = [
            "Check the spelling of the concept term",
            "Try using a different language code",
            "Use broader or more general terms"
        ]
        
        if similar_concepts:
            suggestions.append(f"Consider similar concepts: {', '.join(similar_concepts[:3])}")
        
        if normalized_term and normalized_term != concept:
            suggestions.append(f"Try the normalized form: '{normalized_term}'")
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONCEPT_NOT_FOUND,
            suggestions=suggestions
        )
        
        self.concept = concept
        self.language = language
        self.similar_concepts = similar_concepts or []
        self.normalized_term = normalized_term
        
        # Add concept-specific context
        self.add_context('original_concept', concept)
        self.add_context('language', language)
        self.add_context('normalized_term', normalized_term)
        self.add_context('similar_concepts_count', len(self.similar_concepts))


class InvalidConceptURIError(ConceptNetMCPError):
    """
    Exception raised when a concept URI is malformed or invalid.
    
    This exception is raised when a provided URI does not conform to
    ConceptNet URI format specifications. It provides detailed information
    about the expected format and common formatting mistakes.
    
    Attributes:
        uri: The invalid URI that was provided
        expected_format: Description of the expected URI format
        uri_parts: Parsed components of the invalid URI (if parseable)
        validation_errors: Specific validation errors found
    """
    
    def __init__(
        self,
        uri: str,
        expected_format: Optional[str] = None,
        uri_parts: Optional[Dict[str, str]] = None,
        validation_errors: Optional[List[str]] = None
    ):
        message = f"Invalid concept URI: '{uri}'"
        if expected_format:
            message += f" (expected format: {expected_format})"
        
        suggestions = [
            "Ensure URI starts with '/c/' for concepts or '/r/' for relations",
            "Check that language code is valid (e.g., 'en', 'es', 'fr')",
            "Verify that concept terms are properly URL-encoded",
            "Use normalize_concept_text() to properly format concept terms"
        ]
        
        if expected_format is None:
            expected_format = "/c/{language}/{term} or /r/{relation}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONCEPT_URI_INVALID,
            suggestions=suggestions
        )
        
        self.uri = uri
        self.expected_format = expected_format
        self.uri_parts = uri_parts or {}
        self.validation_errors = validation_errors or []
        
        # Add URI-specific context
        self.add_context('invalid_uri', uri)
        self.add_context('expected_format', expected_format)
        self.add_context('uri_parts', uri_parts)
        self.add_context('validation_errors', validation_errors)


class InvalidLanguageError(ConceptNetMCPError):
    """
    Exception raised when an invalid language code is provided.
    
    This exception is raised when a language code does not conform to
    supported ConceptNet language standards or ISO language code format.
    
    Attributes:
        language: The invalid language code that was provided
        supported_languages: List of supported language codes
        suggested_languages: List of suggested alternative languages
    """
    
    def __init__(
        self,
        language: str,
        supported_languages: Optional[List[str]] = None,
        suggested_languages: Optional[List[str]] = None
    ):
        message = f"Invalid language code: '{language}'"
        
        suggestions = [
            "Use ISO 639-1 language codes (e.g., 'en', 'es', 'fr', 'de')",
            "Check the list of supported ConceptNet languages"
        ]
        
        if suggested_languages:
            suggestions.append(f"Did you mean: {', '.join(suggested_languages[:3])}?")
        
        if supported_languages:
            suggestions.append(f"Supported languages: {', '.join(sorted(supported_languages))}")
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONCEPT_LANGUAGE_INVALID,
            suggestions=suggestions
        )
        
        self.language = language
        self.supported_languages = supported_languages or []
        self.suggested_languages = suggested_languages or []
        
        # Add language-specific context
        self.add_context('invalid_language', language)
        self.add_context('supported_languages_count', len(self.supported_languages))
        self.add_context('suggested_languages', suggested_languages)


class RateLimitExceededError(ConceptNetAPIError):
    """
    Exception raised when ConceptNet API rate limits are exceeded.
    
    This exception is raised when the ConceptNet API returns a 429 status code
    indicating that the rate limit has been exceeded. It provides information
    about when to retry and how to implement proper rate limiting.
    
    Attributes:
        retry_after: Number of seconds to wait before retrying
        limit: The rate limit that was exceeded (requests per time period)
        window: The time window for the rate limit (e.g., "hour", "minute")
        current_usage: Current usage count within the window
    """
    
    def __init__(
        self,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        window: Optional[str] = None,
        current_usage: Optional[int] = None,
        message: Optional[str] = None
    ):
        if message is None:
            message = "ConceptNet API rate limit exceeded"
            if retry_after:
                message += f" (retry after {retry_after} seconds)"
            if limit and window:
                message += f" (limit: {limit} requests per {window})"
        
        suggestions = [
            "Implement exponential backoff in your retry logic",
            "Reduce the frequency of API requests",
            "Cache API responses to minimize redundant requests"
        ]
        
        if retry_after:
            suggestions.insert(0, f"Wait at least {retry_after} seconds before retrying")
        
        super().__init__(
            message=message,
            status_code=429
        )
        self.error_code = ErrorCode.API_RATE_LIMIT_ERROR
        self.suggestions = suggestions
        
        self.retry_after = retry_after
        self.limit = limit
        self.window = window
        self.current_usage = current_usage
        
        # Add rate limit specific context
        self.add_context('retry_after_seconds', retry_after)
        self.add_context('rate_limit', limit)
        self.add_context('rate_window', window)
        self.add_context('current_usage', current_usage)


class NetworkTimeoutError(ConceptNetAPIError):
    """
    Exception raised when network operations timeout.
    
    This exception is raised when API requests exceed the configured
    timeout limits, either for connection establishment or data transfer.
    """
    
    def __init__(
        self,
        timeout_duration: Optional[float] = None,
        operation: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message is None:
            message = "Network operation timed out"
            if operation:
                message += f" during {operation}"
            if timeout_duration:
                message += f" (timeout: {timeout_duration}s)"
        
        suggestions = [
            "Increase the timeout duration for network operations",
            "Check your internet connection stability",
            "Retry the request with exponential backoff",
            "Consider using asynchronous requests for better performance"
        ]
        
        super().__init__(
            message=message,
            error_code=ErrorCode.API_TIMEOUT_ERROR,
            suggestions=suggestions
        )
        
        self.timeout_duration = timeout_duration
        self.operation = operation
        
        self.add_context('timeout_duration', timeout_duration)
        self.add_context('timeout_operation', operation)


class AuthenticationError(ConceptNetAPIError):
    """
    Exception raised when API authentication fails.
    
    This exception is raised when API requests fail due to authentication
    issues, such as invalid API keys or expired tokens.
    """
    
    def __init__(
        self,
        auth_type: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message is None:
            message = "API authentication failed"
            if auth_type:
                message += f" (auth type: {auth_type})"
        
        suggestions = [
            "Verify your API key is correct and active",
            "Check if your API key has expired",
            "Ensure you have permission to access the requested resource",
            "Contact ConceptNet support if the issue persists"
        ]
        
        super().__init__(
            message=message,
            status_code=401,
            error_code=ErrorCode.API_AUTHENTICATION_ERROR,
            suggestions=suggestions
        )
        
        self.auth_type = auth_type
        self.add_context('auth_type', auth_type)


class ValidationError(ConceptNetMCPError):
    """
    Exception raised when data validation fails.
    
    This exception is raised when input data does not pass Pydantic model
    validation, custom validation logic, or parameter constraints. It provides
    detailed information about what went wrong and how to fix it.
    
    Attributes:
        field: The field name that failed validation
        value: The invalid value that was provided
        expected: Description of what was expected
        validator: The name of the validator that failed
        constraints: Any constraints that were violated
    """
    
    def __init__(
        self,
        field: str,
        value: Any,
        expected: str,
        validator: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None
    ):
        message = f"Validation error for field '{field}': {value} (expected: {expected})"
        
        suggestions = [
            f"Ensure '{field}' matches the expected format: {expected}",
            "Check the API documentation for valid parameter values"
        ]
        
        if constraints:
            constraint_desc = ", ".join(f"{k}={v}" for k, v in constraints.items())
            suggestions.append(f"Constraints: {constraint_desc}")
        
        # Determine specific error code based on validation type
        if "required" in expected.lower():
            error_code = ErrorCode.VALIDATION_FIELD_REQUIRED
        elif "type" in expected.lower():
            error_code = ErrorCode.VALIDATION_TYPE_MISMATCH
        elif any(word in expected.lower() for word in ["range", "between", "min", "max"]):
            error_code = ErrorCode.VALIDATION_VALUE_OUT_OF_RANGE
        else:
            error_code = ErrorCode.VALIDATION_FIELD_INVALID
        
        super().__init__(
            message=message,
            error_code=error_code,
            suggestions=suggestions
        )
        
        self.field = field
        self.value = value
        self.expected = expected
        self.validator = validator
        self.constraints = constraints or {}
        
        # Add validation-specific context
        self.add_context('validation_field', field)
        self.add_context('validation_value', str(value))
        self.add_context('validation_expected', expected)
        self.add_context('validator_name', validator)
        self.add_context('constraints', constraints)


class MCPToolError(ConceptNetMCPError):
    """
    Exception raised when MCP tool execution fails.
    
    This exception is raised when an MCP tool encounters an error during
    execution that prevents it from completing successfully. It provides
    detailed information about the tool, parameters, and execution context.
    
    Attributes:
        tool_name: Name of the MCP tool that failed
        tool_parameters: Parameters passed to the tool
        execution_stage: Stage of execution where the error occurred
        inner_exception: The underlying exception that caused the failure
    """
    
    def __init__(
        self,
        tool_name: str,
        error_message: str,
        tool_parameters: Optional[Dict[str, Any]] = None,
        execution_stage: Optional[str] = None,
        inner_exception: Optional[Exception] = None
    ):
        message = f"MCP tool '{tool_name}' failed: {error_message}"
        if execution_stage:
            message += f" (stage: {execution_stage})"
        
        suggestions = [
            "Check the tool parameters for correctness",
            "Verify that required parameters are provided",
            "Review the tool documentation for usage examples"
        ]
        
        if tool_parameters:
            suggestions.append("Validate parameter types and constraints")
        
        super().__init__(
            message=message,
            error_code=ErrorCode.TOOL_EXECUTION_ERROR,
            suggestions=suggestions
        )
        
        self.tool_name = tool_name
        self.error_message = error_message
        self.tool_parameters = tool_parameters or {}
        self.execution_stage = execution_stage
        self.inner_exception = inner_exception
        
        # Add tool-specific context
        self.add_context('tool_name', tool_name)
        self.add_context('execution_stage', execution_stage)
        self.add_context('parameter_count', len(self.tool_parameters))
        
        # Chain the inner exception if provided
        if inner_exception:
            self.__cause__ = inner_exception
            self.add_context('inner_exception_type', type(inner_exception).__name__)
            self.add_context('inner_exception_message', str(inner_exception))


class PaginationError(ConceptNetMCPError):
    """
    Exception raised when pagination operations fail.
    
    This exception is raised when there are issues with fetching paginated
    results, merging responses, or handling pagination metadata. It provides
    information about partial results and recovery options.
    
    Attributes:
        page_url: URL of the page that failed to load
        page_number: Page number that failed (if applicable)
        total_pages: Total number of pages expected
        partial_results: Results successfully retrieved before the error
        pagination_metadata: Metadata about the pagination state
    """
    
    def __init__(
        self,
        message: str,
        page_url: Optional[str] = None,
        page_number: Optional[int] = None,
        total_pages: Optional[int] = None,
        partial_results: Optional[List] = None,
        pagination_metadata: Optional[Dict[str, Any]] = None
    ):
        suggestions = [
            "Retry the pagination request",
            "Check if the page URL is valid and accessible",
            "Verify pagination parameters (offset, limit)"
        ]
        
        if partial_results:
            suggestions.append(f"Use partial results ({len(partial_results)} items)")
        
        # Determine specific error code based on the error
        if "offset" in message.lower():
            error_code = ErrorCode.PAGINATION_INVALID_OFFSET
        elif "limit" in message.lower():
            error_code = ErrorCode.PAGINATION_INVALID_LIMIT
        elif "page not found" in message.lower():
            error_code = ErrorCode.PAGINATION_PAGE_NOT_FOUND
        elif "merge" in message.lower():
            error_code = ErrorCode.PAGINATION_MERGE_ERROR
        else:
            error_code = ErrorCode.PAGINATION_INVALID_OFFSET  # Default
        
        super().__init__(
            message=message,
            error_code=error_code,
            suggestions=suggestions
        )
        
        self.page_url = page_url
        self.page_number = page_number
        self.total_pages = total_pages
        self.partial_results = partial_results or []
        self.pagination_metadata = pagination_metadata or {}
        
        # Add pagination-specific context
        self.add_context('failed_page_url', page_url)
        self.add_context('failed_page_number', page_number)
        self.add_context('total_pages', total_pages)
        self.add_context('partial_results_count', len(self.partial_results))
        self.add_context('pagination_metadata', pagination_metadata)


class ConfigurationError(ConceptNetMCPError):
    """
    Exception raised when server configuration is invalid or missing.
    
    This exception is raised when the ConceptNet MCP server encounters
    configuration problems that prevent it from operating correctly.
    
    Attributes:
        config_key: The configuration key that is invalid
        config_value: The invalid configuration value
        config_file: Path to the configuration file (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        config_file: Optional[str] = None
    ):
        suggestions = [
            "Check the server configuration file",
            "Verify all required configuration parameters are set",
            "Ensure configuration values are in the correct format"
        ]
        
        if config_key:
            suggestions.append(f"Review the '{config_key}' configuration setting")
        
        if config_file:
            suggestions.append(f"Check configuration file: {config_file}")
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            suggestions=suggestions
        )
        
        self.config_key = config_key
        self.config_value = config_value
        self.config_file = config_file
        
        # Add configuration-specific context
        self.add_context('config_key', config_key)
        self.add_context('config_value', str(config_value) if config_value is not None else None)
        self.add_context('config_file', config_file)


class TextValidationError(ConceptNetMCPError):
    """
    Exception raised for text validation failures.
    
    This exception is raised when text content fails validation rules,
    such as invalid format, prohibited characters, or security constraints.
    
    Attributes:
        text: The invalid text that was provided
        expected_format: Description of the expected text format
        validation_rule: The specific validation rule that failed
    """
    
    def __init__(
        self,
        message: str,
        text: str,
        reason: str,
        validation_rule: Optional[str] = None
    ):
        suggestions = [
            f"Fix the validation issue: {reason}",
            "Remove any invalid or prohibited characters",
            "Check text length and content constraints"
        ]
        
        if validation_rule:
            suggestions.append(f"Review validation rule: {validation_rule}")
        
        super().__init__(
            message=message,
            error_code=ErrorCode.TEXT_VALIDATION_ERROR,
            suggestions=suggestions
        )
        
        self.text = text
        self.reason = reason
        self.validation_rule = validation_rule
        
        # Add text-specific context
        self.add_context('invalid_text', text[:100] + "..." if len(text) > 100 else text)
        self.add_context('reason', reason)
        self.add_context('validation_rule', validation_rule)


class URIValidationError(ConceptNetMCPError):
    """
    Exception raised for URI format validation errors.
    
    This exception is raised when URI strings fail format validation,
    such as invalid characters, malformed structure, or security issues.
    
    Attributes:
        uri: The invalid URI that was provided
        expected_format: Description of the expected URI format
        validation_errors: List of specific validation errors found
    """
    
    def __init__(
        self,
        message: str,
        uri: str,
        reason: str,
        validation_errors: Optional[List[str]] = None
    ):
        suggestions = [
            f"Fix the validation issue: {reason}",
            "Check for invalid characters or encoding issues",
            "Verify URI structure and components"
        ]
        
        if validation_errors:
            suggestions.extend([f"Fix validation error: {error}" for error in validation_errors[:3]])
        
        super().__init__(
            message=message,
            error_code=ErrorCode.URI_VALIDATION_ERROR,
            suggestions=suggestions
        )
        
        self.uri = uri
        self.reason = reason
        self.validation_errors = validation_errors or []
        
        # Add URI-specific context
        self.add_context('invalid_uri', uri)
        self.add_context('reason', reason)
        self.add_context('validation_errors', validation_errors)


# Utility functions for common exception scenarios

def create_concept_not_found_error(
    concept: str,
    language: str = "en",
    similar_concepts: Optional[List[str]] = None
) -> ConceptNotFoundError:
    """
    Create a ConceptNotFoundError with helpful suggestions.
    
    Args:
        concept: The concept that was not found
        language: Language code used in the search
        similar_concepts: List of similar concepts found
        
    Returns:
        Configured ConceptNotFoundError instance
    """
    return ConceptNotFoundError(
        concept=concept,
        language=language,
        similar_concepts=similar_concepts
    )


def create_validation_error(
    field: str,
    value: Any,
    expected_type: Union[type, str],
    constraints: Optional[Dict[str, Any]] = None
) -> ValidationError:
    """
    Create a ValidationError with type information.
    
    Args:
        field: Field name that failed validation
        value: Invalid value provided
        expected_type: Expected type or description
        constraints: Additional constraints that were violated
        
    Returns:
        Configured ValidationError instance
    """
    if isinstance(expected_type, type):
        expected = expected_type.__name__
    else:
        expected = str(expected_type)
    
    return ValidationError(
        field=field,
        value=value,
        expected=expected,
        constraints=constraints
    )


def create_api_error_from_response(
    response,  # requests.Response
    endpoint: Optional[str] = None,
    method: Optional[str] = None
) -> ConceptNetAPIError:
    """
    Create a ConceptNetAPIError from an HTTP response.
    
    Args:
        response: HTTP response object
        endpoint: API endpoint that was called
        method: HTTP method used
        
    Returns:
        Configured ConceptNetAPIError instance
    """
    try:
        response_data = response.json()
    except Exception:
        response_data = {"error": response.text}
    
    message = f"API request failed with status {response.status_code}"
    if "error" in response_data:
        message += f": {response_data['error']}"
    
    return ConceptNetAPIError(
        message=message,
        status_code=response.status_code,
        response_data=response_data,
        endpoint=endpoint,
        method=method,
        request_id=response.headers.get('X-Request-ID')
    )


# Exception registry for programmatic access
EXCEPTION_REGISTRY = {
    ErrorCode.UNKNOWN_ERROR: ConceptNetMCPError,
    ErrorCode.CONFIGURATION_ERROR: ConfigurationError,
    ErrorCode.INTERNAL_ERROR: ConceptNetMCPError,
    ErrorCode.API_CONNECTION_ERROR: ConceptNetAPIError,
    ErrorCode.API_TIMEOUT_ERROR: NetworkTimeoutError,
    ErrorCode.API_RATE_LIMIT_ERROR: RateLimitExceededError,
    ErrorCode.API_AUTHENTICATION_ERROR: AuthenticationError,
    ErrorCode.API_SERVER_ERROR: ConceptNetAPIError,
    ErrorCode.API_CLIENT_ERROR: ConceptNetAPIError,
    ErrorCode.CONCEPT_NOT_FOUND: ConceptNotFoundError,
    ErrorCode.CONCEPT_URI_INVALID: InvalidConceptURIError,
    ErrorCode.CONCEPT_LANGUAGE_INVALID: InvalidLanguageError,
    ErrorCode.CONCEPT_TERM_INVALID: ConceptNetMCPError,
    ErrorCode.VALIDATION_FIELD_REQUIRED: ValidationError,
    ErrorCode.VALIDATION_FIELD_INVALID: ValidationError,
    ErrorCode.VALIDATION_TYPE_MISMATCH: ValidationError,
    ErrorCode.VALIDATION_VALUE_OUT_OF_RANGE: ValidationError,
    ErrorCode.TOOL_EXECUTION_ERROR: MCPToolError,
    ErrorCode.TOOL_PARAMETER_ERROR: MCPToolError,
    ErrorCode.TOOL_TIMEOUT_ERROR: MCPToolError,
    ErrorCode.PAGINATION_INVALID_OFFSET: PaginationError,
    ErrorCode.PAGINATION_INVALID_LIMIT: PaginationError,
    ErrorCode.PAGINATION_PAGE_NOT_FOUND: PaginationError,
    ErrorCode.PAGINATION_MERGE_ERROR: PaginationError,
    ErrorCode.TEXT_VALIDATION_ERROR: TextValidationError,
    ErrorCode.URI_VALIDATION_ERROR: URIValidationError,
}


def get_exception_for_error_code(error_code: ErrorCode) -> type:
    """
    Get the appropriate exception class for an error code.
    
    Args:
        error_code: The error code to look up
        
    Returns:
        Exception class for the error code
    """
    return EXCEPTION_REGISTRY.get(error_code, ConceptNetMCPError)
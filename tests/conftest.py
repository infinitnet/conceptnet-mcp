"""
Pytest configuration and fixtures for the ConceptNet MCP utility tests.

This module provides shared fixtures, test configuration, and common utilities
for all test modules in the test suite.
"""

import pytest
import tempfile
import os
import logging
import sys
from pathlib import Path
from unittest.mock import patch

# Add the src directory to Python path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment before running tests."""
    # Ensure clean logging state
    logging.getLogger().handlers.clear()
    logging.basicConfig(level=logging.WARNING)  # Reduce test noise
    
    # Clear any existing module caches that might interfere
    modules_to_clear = [
        mod for mod in sys.modules.keys() 
        if mod.startswith('src.conceptnet_mcp.utils')
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]
    
    yield
    
    # Cleanup after all tests
    logging.getLogger().handlers.clear()


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_log_file(temp_directory):
    """Provide a temporary log file for testing."""
    log_file = temp_directory / "test.log"
    yield str(log_file)
    
    # Cleanup
    if log_file.exists():
        log_file.unlink()


@pytest.fixture
def sample_concept_texts():
    """Provide sample concept texts for testing."""
    return {
        'simple': 'hello',
        'multi_word': 'hello world',
        'with_punctuation': 'hello, world!',
        'with_unicode': 'café',
        'with_diacritics': 'naïve résumé',
        'mixed_case': 'Hello WORLD',
        'with_numbers': 'hello123',
        'japanese': '東京',
        'arabic': 'العربية',
        'cyrillic': 'Москва',
        'long_text': 'this is a very long concept text that exceeds normal limits' * 5,
        'empty': '',
        'whitespace_only': '   ',
        'special_chars': '!@#$%^&*()',
        'with_underscores': 'hello_world_test',
        'with_hyphens': 'multi-word-concept',
    }


@pytest.fixture
def sample_language_codes():
    """Provide sample language codes for testing."""
    return {
        'valid': ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 
                 'ar', 'hi', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'cs', 'hu',
                 'en-us', 'en-gb', 'zh-cn', 'zh-tw', 'pt-br', 'es-es'],
        'invalid': ['', 'x', 'xyz', 'english', 'ENGLISH', 'EN', '123', 
                   'en_us', 'en/us', 'en us', 'toolongcode'],
        'edge_cases': ['a', 'zz', '1a', 'a1', 'en-', '-en', 'en--us']
    }


@pytest.fixture
def sample_uris():
    """Provide sample ConceptNet URIs for testing."""
    return {
        'valid': [
            '/c/en/hello',
            '/c/es/hola',
            '/c/en/hello_world',
            '/c/fr/café',
            '/c/ja/東京',
            '/c/zh-cn/test',
            '/c/pt-br/teste'
        ],
        'invalid': [
            '/c/en',           # Missing term
            '/c',              # Missing language and term
            '/x/en/test',      # Wrong prefix
            'c/en/test',       # Missing leading slash
            '/c//test',        # Empty language
            '/c/en/',          # Empty term
            '',                # Empty string
            'not-a-uri',       # Not a URI format
            '/concept/en/test' # Wrong format
        ],
        'edge_cases': [
            '/c/en/a',         # Very short term
            f'/c/en/{"a" * 200}',  # Very long term
            '/c/en/test123',   # Term with numbers
            '/c/en/test_with_underscores'  # Term with underscores
        ]
    }


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger_instance = mock_get_logger.return_value
        yield mock_logger_instance


@pytest.fixture
def suppress_logging():
    """Suppress logging output during tests."""
    # Store original level
    original_level = logging.getLogger().level
    
    # Set to CRITICAL to suppress most logs
    logging.getLogger().setLevel(logging.CRITICAL)
    
    yield
    
    # Restore original level
    logging.getLogger().setLevel(original_level)


@pytest.fixture
def clean_cache():
    """Clear function caches before and after tests."""
    # Import the modules to clear their caches
    try:
        from src.conceptnet_mcp.utils.text_utils import normalize_concept_text, validate_language_code
        
        # Clear caches before test
        if hasattr(normalize_concept_text, 'cache_clear'):
            normalize_concept_text.cache_clear()
        if hasattr(validate_language_code, 'cache_clear'):
            validate_language_code.cache_clear()
        
        yield
        
        # Clear caches after test
        if hasattr(normalize_concept_text, 'cache_clear'):
            normalize_concept_text.cache_clear()
        if hasattr(validate_language_code, 'cache_clear'):
            validate_language_code.cache_clear()
            
    except ImportError:
        # If modules aren't available, just yield
        yield


@pytest.fixture
def exception_samples():
    """Provide sample exceptions for testing."""
    from src.conceptnet_mcp.utils.exceptions import (
        ConceptNetMCPError,
        ConceptNotFoundError,
        InvalidConceptURIError,
        ValidationError,
        ErrorCode
    )
    
    return {
        'base_error': ConceptNetMCPError("Test error"),
        'concept_not_found': ConceptNotFoundError("test_concept"),
        'invalid_uri': InvalidConceptURIError("/invalid/uri"),
        'validation_error': ValidationError("field", "value", "expected"),
        'with_context': ConceptNetMCPError("Test").add_context("key", "value"),
        'with_suggestions': ConceptNetMCPError("Test").add_suggestion("Try this"),
    }


@pytest.fixture
def performance_test_data():
    """Provide data for performance testing."""
    return {
        'small_text': "hello world",
        'medium_text': "this is a medium length text " * 10,
        'large_text': "this is a large text " * 100,
        'unicode_text': "café naïve résumé " * 50,
        'mixed_script': "hello 東京 world Москва test " * 20,
    }


@pytest.fixture(params=[
    ("hello world", "en", "/c/en/hello_world"),
    ("café", "fr", "/c/fr/café"),
    ("東京", "ja", "/c/ja/東京"),
    ("test123", "en", "/c/en/test123"),
])
def concept_uri_test_case(request):
    """Parametrized fixture for concept URI test cases."""
    text, language, expected_uri = request.param
    return {
        'text': text,
        'language': language,
        'expected_uri': expected_uri
    }


@pytest.fixture
def logging_test_setup(temp_log_file):
    """Set up logging configuration for testing."""
    # Store original handlers
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    # Clear handlers
    root_logger.handlers.clear()
    
    yield {
        'log_file': temp_log_file,
        'root_logger': root_logger
    }
    
    # Restore original configuration
    root_logger.handlers[:] = original_handlers
    root_logger.setLevel(original_level)


class TestUtilities:
    """Utility class with helper methods for tests."""
    
    @staticmethod
    def assert_valid_json(json_string):
        """Assert that a string is valid JSON."""
        import json
        try:
            json.loads(json_string)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def assert_no_sensitive_data(text, sensitive_patterns=None):
        """Assert that text doesn't contain sensitive data patterns."""
        if sensitive_patterns is None:
            sensitive_patterns = [
                'password', 'secret', 'token', 'key', 'api_key',
                'private', 'confidential', 'admin', 'root'
            ]
        
        text_lower = text.lower()
        for pattern in sensitive_patterns:
            assert pattern not in text_lower, f"Sensitive pattern '{pattern}' found in text"
    
    @staticmethod
    def assert_uri_format(uri):
        """Assert that a string follows ConceptNet URI format."""
        import re
        pattern = r'^/c/[a-z]{2}(-[a-z]{2})?/[^/]+$'
        assert re.match(pattern, uri), f"URI '{uri}' doesn't match expected format"
    
    @staticmethod
    def count_unicode_categories(text):
        """Count characters by Unicode category."""
        import unicodedata
        categories = {}
        for char in text:
            category = unicodedata.category(char)
            categories[category] = categories.get(category, 0) + 1
        return categories


@pytest.fixture
def test_utilities():
    """Provide test utility methods."""
    return TestUtilities


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-related tests"
    )


# Pytest hooks for enhanced test reporting
def pytest_runtest_setup(item):
    """Hook called before each test runs."""
    # Add test name to logging context if needed
    pass


def pytest_runtest_teardown(item, nextitem):
    """Hook called after each test runs."""
    # Clear any test-specific state
    pass


def pytest_collection_modifyitems(config, items):
    """Hook to modify test collection."""
    # Auto-mark tests based on their location or names
    for item in items:
        # Mark slow tests
        if "slow" in item.name.lower() or "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark security tests
        if "security" in item.name.lower() or "injection" in item.name.lower():
            item.add_marker(pytest.mark.security)


# Skip tests based on conditions
def pytest_runtest_setup(item):
    """Skip tests based on various conditions."""
    # Skip slow tests in CI if specified
    if item.get_closest_marker("slow"):
        if os.environ.get("SKIP_SLOW_TESTS"):
            pytest.skip("Skipping slow test in CI environment")
    
    # Skip tests that require specific dependencies
    if item.get_closest_marker("requires_network"):
        # Check network connectivity or skip
        pass
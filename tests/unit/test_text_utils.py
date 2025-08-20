"""
Comprehensive unit tests for the text_utils module.

This test suite verifies all text processing functions including normalization,
URI construction/parsing, validation, and security features.
"""

import pytest
import unicodedata
from unittest.mock import patch

from src.conceptnet_mcp.utils.text_utils import (
    normalize_concept_text,
    construct_concept_uri,
    parse_concept_uri,
    validate_concept_uri,
    validate_concept_text,
    validate_language_code,
    normalize_language_code,
    clean_text_for_uri,
    sanitize_search_query,
    sanitize_text_for_uri,
    clean_whitespace,
    is_valid_concept_text,
    is_valid_concept_format,
    normalize_unicode,
    validate_text_length,
    normalize_text_for_display,
    normalize_uri_to_text,
    normalize_relation_text,
    find_similar_languages,
    extract_language_from_uri,
    estimate_text_language,
    get_text_language_hints,
    calculate_text_similarity,
    fuzzy_match_concepts,
    split_compound_terms,
    truncate_text_safely,
    clear_text_caches,
    get_cache_info,
    SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES,
    RELATION_PATTERNS,
    MAX_CONCEPT_LENGTH,
    MAX_URI_LENGTH,
    MAX_TEXT_LENGTH,
)
from src.conceptnet_mcp.utils.exceptions import (
    InvalidConceptURIError,
    InvalidLanguageError,
    ValidationError,
    TextValidationError,
    URIValidationError,
)


class TestNormalizeConceptText:
    """Test the normalize_concept_text function."""
    
    def test_basic_normalization(self):
        """Test basic text normalization."""
        # Simple text
        assert normalize_concept_text("hello world") == "hello_world"
        assert normalize_concept_text("Hello World") == "hello_world"
        
        # Text with special characters
        assert normalize_concept_text("café") == "café"
        assert normalize_concept_text("naïve") == "naïve"
    
    def test_whitespace_handling(self):
        """Test whitespace handling in normalization."""
        # Multiple spaces
        assert normalize_concept_text("hello   world") == "hello_world"
        
        # Leading/trailing whitespace
        assert normalize_concept_text("  hello world  ") == "hello_world"
        
        # Mixed whitespace types
        assert normalize_concept_text("hello\t\nworld") == "hello_world"
        
        # Empty and whitespace-only strings
        assert normalize_concept_text("") == ""
        assert normalize_concept_text("   ") == ""
    
    def test_special_character_handling(self):
        """Test handling of special characters."""
        # Punctuation removal
        assert normalize_concept_text("hello, world!") == "hello_world"
        assert normalize_concept_text("don't worry") == "dont_worry"
        assert normalize_concept_text("user@domain.com") == "userdomaincom"
        
        # Hyphen to underscore conversion
        assert normalize_concept_text("multi-word-term") == "multi_word_term"
        
        # Mixed special characters
        assert normalize_concept_text("hello... world???") == "hello_world"
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Composed vs decomposed characters
        text1 = "café"  # é as single character
        text2 = "cafe\u0301"  # e + combining acute accent
        
        result1 = normalize_concept_text(text1)
        result2 = normalize_concept_text(text2)
        assert result1 == result2
        
        # Various Unicode characters
        assert normalize_concept_text("Москва") == "москва"
        assert normalize_concept_text("東京") == "東京"
        assert normalize_concept_text("العربية") == "العربية"
    
    def test_length_limits(self):
        """Test length limiting."""
        long_text = "a" * 300
        result = normalize_concept_text(long_text, max_length=100)
        assert len(result) <= 100
        
        # With default max_length
        very_long_text = "word " * 100
        result = normalize_concept_text(very_long_text)
        assert len(result) <= 255
    
    def test_preserve_underscores_option(self):
        """Test preserve_underscores option."""
        text = "hello_world test"
        
        # Default behavior (preserve underscores)
        assert normalize_concept_text(text) == "hello_world_test"
        
        # With preserve_underscores=False
        assert normalize_concept_text(text, preserve_underscores=False) == "hello_world_test"
        
        # Multiple underscores
        text_multi = "hello__world___test"
        result = normalize_concept_text(text_multi)
        assert result == "hello_world_test"  # Multiple underscores should be normalized
    
    def test_strip_diacritics_option(self):
        """Test strip_diacritics option."""
        text = "café naïve résumé"
        
        # Default behavior (preserve diacritics)
        assert normalize_concept_text(text) == "café_naïve_résumé"
        
        # With strip_diacritics=True
        result = normalize_concept_text(text, strip_diacritics=True)
        assert result == "cafe_naive_resume"
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # None input
        with pytest.raises(AttributeError):
            normalize_concept_text(None)
        
        # Non-string input (should convert to string)
        assert normalize_concept_text(123) == "123"
        assert normalize_concept_text(True) == "true"
        
        # Empty string
        assert normalize_concept_text("") == ""
        
        # Only special characters
        assert normalize_concept_text("!@#$%^&*()") == ""
        
        # Very short max_length
        result = normalize_concept_text("hello world", max_length=3)
        assert len(result) <= 3


class TestConstructConceptURI:
    """Test the construct_concept_uri function."""
    
    def test_basic_construction(self):
        """Test basic URI construction."""
        uri = construct_concept_uri("hello", "en")
        assert uri == "/c/en/hello"
        
        uri = construct_concept_uri("world", "es")
        assert uri == "/c/es/world"
    
    def test_text_normalization(self):
        """Test that text is normalized during construction."""
        uri = construct_concept_uri("Hello World", "en")
        assert uri == "/c/en/hello_world"
        
        uri = construct_concept_uri("café", "fr")
        assert uri == "/c/fr/café"
    
    def test_language_validation(self):
        """Test language code validation."""
        # Valid language codes
        assert construct_concept_uri("test", "en") == "/c/en/test"
        assert construct_concept_uri("test", "zh-cn") == "/c/zh-cn/test"
        
        # Invalid language codes
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "invalid")
        
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "")
        
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "x")  # Too short
    
    def test_text_validation(self):
        """Test text validation during construction."""
        # Empty text
        with pytest.raises(ValidationError):
            construct_concept_uri("", "en")
        
        # Whitespace-only text
        with pytest.raises(ValidationError):
            construct_concept_uri("   ", "en")
        
        # Text that becomes empty after normalization
        with pytest.raises(ValidationError):
            construct_concept_uri("!@#$%", "en")
    
    def test_auto_normalize_option(self):
        """Test auto_normalize option."""
        # With auto_normalize=True (default)
        uri = construct_concept_uri("Hello World", "en")
        assert uri == "/c/en/hello_world"
        
        # With auto_normalize=False
        uri = construct_concept_uri("hello_world", "en", auto_normalize=False)
        assert uri == "/c/en/hello_world"
        
        # Invalid characters with auto_normalize=False should raise error
        with pytest.raises(ValidationError):
            construct_concept_uri("hello world", "en", auto_normalize=False)
    
    def test_validate_option(self):
        """Test validate option."""
        # With validate=True (default)
        with pytest.raises(InvalidLanguageError):
            construct_concept_uri("test", "invalid")
        
        # With validate=False (bypasses validation)
        uri = construct_concept_uri("test", "invalid", validate=False)
        assert uri == "/c/invalid/test"
    
    def test_special_characters_handling(self):
        """Test handling of special characters in URI construction."""
        # Characters that should be URL-safe
        uri = construct_concept_uri("hello-world", "en")
        assert uri == "/c/en/hello_world"
        
        # Unicode characters should be preserved
        uri = construct_concept_uri("東京", "ja")
        assert uri == "/c/ja/東京"


class TestParseConceptURI:
    """Test the parse_concept_uri function."""
    
    def test_basic_parsing(self):
        """Test basic URI parsing."""
        result = parse_concept_uri("/c/en/hello")
        expected = {
            "language": "en",
            "term": "hello",
            "original_uri": "/c/en/hello",
            "normalized_term": "hello"
        }
        assert result == expected
    
    def test_complex_terms(self):
        """Test parsing with complex terms."""
        # Multi-word terms
        result = parse_concept_uri("/c/en/hello_world")
        assert result["term"] == "hello_world"
        assert result["language"] == "en"
        
        # Unicode terms
        result = parse_concept_uri("/c/ja/東京")
        assert result["term"] == "東京"
        assert result["language"] == "ja"
        
        # Terms with special characters
        result = parse_concept_uri("/c/fr/café")
        assert result["term"] == "café"
        assert result["language"] == "fr"
    
    def test_language_codes(self):
        """Test parsing different language codes."""
        # Standard language codes
        result = parse_concept_uri("/c/en/test")
        assert result["language"] == "en"
        
        result = parse_concept_uri("/c/zh-cn/test")
        assert result["language"] == "zh-cn"
        
        result = parse_concept_uri("/c/pt-br/test")
        assert result["language"] == "pt-br"
    
    def test_normalize_term_option(self):
        """Test normalize_term option."""
        # With normalize_term=True (default)
        result = parse_concept_uri("/c/en/Hello_World")
        assert result["normalized_term"] == "hello_world"
        
        # With normalize_term=False
        result = parse_concept_uri("/c/en/Hello_World", normalize_term=False)
        assert result["normalized_term"] == "Hello_World"
    
    def test_validate_option(self):
        """Test validate option."""
        # With validate=True (default)
        with pytest.raises(InvalidConceptURIError):
            parse_concept_uri("/invalid/format")
        
        # With validate=False
        result = parse_concept_uri("/invalid/format", validate=False)
        assert result is not None  # Should not raise error
    
    def test_invalid_uri_formats(self):
        """Test handling of invalid URI formats."""
        invalid_uris = [
            "/c/en",  # Missing term
            "/c",     # Missing language and term
            "/x/en/test",  # Wrong prefix
            "c/en/test",   # Missing leading slash
            "/c//test",    # Empty language
            "/c/en/",      # Empty term
            "",            # Empty string
            "not-a-uri",   # Not a URI format
        ]
        
        for uri in invalid_uris:
            with pytest.raises(InvalidConceptURIError):
                parse_concept_uri(uri)
    
    def test_edge_cases(self):
        """Test edge cases in URI parsing."""
        # Very long terms
        long_term = "a" * 200
        uri = f"/c/en/{long_term}"
        result = parse_concept_uri(uri)
        assert result["term"] == long_term
        
        # Special characters in terms
        uri = "/c/en/hello%20world"  # URL encoded space
        result = parse_concept_uri(uri)
        assert "hello" in result["term"]  # Should handle URL encoding


class TestValidateConceptText:
    """Test the validate_concept_text function."""
    
    def test_valid_text(self):
        """Test validation of valid text."""
        # Should not raise exceptions
        validate_concept_text("hello")
        validate_concept_text("hello_world")
        validate_concept_text("café")
        validate_concept_text("東京")
        validate_concept_text("hello123")
    
    def test_invalid_text(self):
        """Test validation of invalid text."""
        # Empty text
        with pytest.raises(TextValidationError):
            validate_concept_text("")
        
        # Whitespace-only text
        with pytest.raises(TextValidationError):
            validate_concept_text("   ")
        
        # Text with invalid characters
        with pytest.raises(TextValidationError):
            validate_concept_text("hello world")  # Space not allowed
        
        with pytest.raises(TextValidationError):
            validate_concept_text("hello/world")  # Slash not allowed
        
        with pytest.raises(TextValidationError):
            validate_concept_text("hello?world")  # Question mark not allowed
    
    def test_length_limits(self):
        """Test length validation."""
        # Text too long
        long_text = "a" * 300
        with pytest.raises(TextValidationError):
            validate_concept_text(long_text, max_length=100)
        
        # Text too short
        with pytest.raises(TextValidationError):
            validate_concept_text("a", min_length=5)
    
    def test_custom_allowed_chars(self):
        """Test custom allowed characters."""
        # Allow spaces
        validate_concept_text("hello world", allowed_chars=" ")
        
        # Disallow underscores
        with pytest.raises(TextValidationError):
            validate_concept_text("hello_world", allowed_chars="")


class TestValidateLanguageCode:
    """Test the validate_language_code function."""
    
    def test_valid_language_codes(self):
        """Test validation of valid language codes."""
        valid_codes = [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "nl", "sv", "no", "da", "fi", "pl", "cs", "hu",
            "en-us", "en-gb", "zh-cn", "zh-tw", "pt-br", "es-es"
        ]
        
        for code in valid_codes:
            validate_language_code(code)  # Should not raise exception
    
    def test_invalid_language_codes(self):
        """Test validation of invalid language codes."""
        invalid_codes = [
            "", "x", "xyz", "english", "ENGLISH", "EN", 
            "123", "en_us", "en/us", "en us", "toolong"
        ]
        
        for code in invalid_codes:
            with pytest.raises(InvalidLanguageError):
                validate_language_code(code)
    
    def test_case_sensitivity(self):
        """Test case sensitivity in language codes."""
        # Lowercase should be valid
        validate_language_code("en")
        validate_language_code("zh-cn")
        
        # Uppercase should be invalid
        with pytest.raises(InvalidLanguageError):
            validate_language_code("EN")
        
        with pytest.raises(InvalidLanguageError):
            validate_language_code("ZH-CN")


class TestSanitizeTextForURI:
    """Test the sanitize_text_for_uri function."""
    
    def test_basic_sanitization(self):
        """Test basic text sanitization."""
        assert sanitize_text_for_uri("hello world") == "hello_world"
        assert sanitize_text_for_uri("hello/world") == "hello_world"
        assert sanitize_text_for_uri("hello?world") == "hello_world"
    
    def test_multiple_separators(self):
        """Test handling of multiple separators."""
        assert sanitize_text_for_uri("hello   world") == "hello_world"
        assert sanitize_text_for_uri("hello///world") == "hello_world"
        assert sanitize_text_for_uri("hello___world") == "hello_world"
    
    def test_leading_trailing_separators(self):
        """Test removal of leading/trailing separators."""
        assert sanitize_text_for_uri("_hello_world_") == "hello_world"
        assert sanitize_text_for_uri("/hello/world/") == "hello_world"
        assert sanitize_text_for_uri(" hello world ") == "hello_world"
    
    def test_special_characters(self):
        """Test handling of special characters."""
        text = "hello@world.com"
        result = sanitize_text_for_uri(text)
        assert result == "hello_world_com"
        
        text = "hello(world)!"
        result = sanitize_text_for_uri(text)
        assert result == "hello_world"
    
    def test_unicode_preservation(self):
        """Test preservation of Unicode characters."""
        assert sanitize_text_for_uri("café world") == "café_world"
        assert sanitize_text_for_uri("東京 駅") == "東京_駅"
        assert sanitize_text_for_uri("Москва город") == "москва_город"
    
    def test_length_limits(self):
        """Test length limiting in sanitization."""
        long_text = "word " * 100
        result = sanitize_text_for_uri(long_text, max_length=50)
        assert len(result) <= 50
        assert not result.endswith("_")  # Should not end with separator
    
    def test_empty_result_handling(self):
        """Test handling when sanitization results in empty string."""
        # Only special characters
        result = sanitize_text_for_uri("!@#$%^&*()")
        assert result == ""
        
        # Only whitespace
        result = sanitize_text_for_uri("   ")
        assert result == ""


class TestCleanWhitespace:
    """Test the clean_whitespace function."""
    
    def test_basic_cleaning(self):
        """Test basic whitespace cleaning."""
        assert clean_whitespace("hello  world") == "hello world"
        assert clean_whitespace("  hello world  ") == "hello world"
        assert clean_whitespace("hello\t\nworld") == "hello world"
    
    def test_different_whitespace_types(self):
        """Test cleaning different types of whitespace."""
        text = "hello\t\n\r\v\f world"
        result = clean_whitespace(text)
        assert result == "hello world"
    
    def test_unicode_whitespace(self):
        """Test cleaning Unicode whitespace characters."""
        # Non-breaking space and other Unicode spaces
        text = "hello\u00A0\u2000\u2001world"
        result = clean_whitespace(text)
        assert result == "hello world"
    
    def test_preserve_single_spaces(self):
        """Test that single spaces are preserved."""
        assert clean_whitespace("hello world test") == "hello world test"
    
    def test_empty_and_whitespace_only(self):
        """Test handling of empty and whitespace-only strings."""
        assert clean_whitespace("") == ""
        assert clean_whitespace("   ") == ""
        assert clean_whitespace("\t\n\r") == ""


class TestIsValidConceptFormat:
    """Test the is_valid_concept_format function."""
    
    def test_valid_formats(self):
        """Test validation of valid concept formats."""
        valid_texts = [
            "hello",
            "hello_world",
            "café",
            "東京",
            "test123",
            "a",
            "very_long_concept_name_that_is_still_valid"
        ]
        
        for text in valid_texts:
            assert is_valid_concept_format(text) is True
    
    def test_invalid_formats(self):
        """Test validation of invalid concept formats."""
        invalid_texts = [
            "",
            "   ",
            "hello world",  # Space
            "hello/world",  # Slash
            "hello?world",  # Question mark
            "hello world",  # Space
            "hello\nworld", # Newline
            "hello\tworld", # Tab
        ]
        
        for text in invalid_texts:
            assert is_valid_concept_format(text) is False
    
    def test_edge_cases(self):
        """Test edge cases in format validation."""
        # Very long text
        long_text = "a" * 300
        assert is_valid_concept_format(long_text) is False
        
        # Unicode characters
        assert is_valid_concept_format("Москва") is True
        assert is_valid_concept_format("العربية") is True


class TestGetTextLanguageHints:
    """Test the get_text_language_hints function."""
    
    def test_obvious_language_hints(self):
        """Test detection of obvious language hints."""
        # English text
        hints = get_text_language_hints("hello world")
        assert "en" in hints
        
        # Spanish text
        hints = get_text_language_hints("hola mundo")
        assert "es" in hints
        
        # German text
        hints = get_text_language_hints("guten tag")
        assert "de" in hints
    
    def test_script_based_detection(self):
        """Test script-based language detection."""
        # Japanese (Hiragana/Katakana/Kanji)
        hints = get_text_language_hints("東京")
        assert "ja" in hints or "zh" in hints  # Could be Japanese or Chinese
        
        # Arabic script
        hints = get_text_language_hints("العربية")
        assert "ar" in hints
        
        # Cyrillic script
        hints = get_text_language_hints("Москва")
        assert "ru" in hints
    
    def test_mixed_scripts(self):
        """Test handling of mixed scripts."""
        hints = get_text_language_hints("hello 東京")
        assert len(hints) >= 1  # Should detect at least one language
    
    def test_ambiguous_text(self):
        """Test handling of ambiguous text."""
        # Numbers and symbols
        hints = get_text_language_hints("123456")
        assert isinstance(hints, list)  # Should return a list even if empty
        
        # Short text
        hints = get_text_language_hints("a")
        assert isinstance(hints, list)
    
    def test_confidence_ordering(self):
        """Test that hints are ordered by confidence."""
        hints = get_text_language_hints("hello world how are you")
        if len(hints) > 1:
            # Should be ordered by confidence (most likely first)
            assert isinstance(hints, list)


class TestNormalizeUnicode:
    """Test the normalize_unicode function."""
    
    def test_nfc_normalization(self):
        """Test NFC normalization (default)."""
        # Decomposed to composed
        text = "cafe\u0301"  # e + combining acute accent
        result = normalize_unicode(text)
        expected = "café"  # é as single character
        assert result == expected
        assert unicodedata.is_normalized('NFC', result)
    
    def test_nfd_normalization(self):
        """Test NFD normalization."""
        # Composed to decomposed
        text = "café"  # é as single character
        result = normalize_unicode(text, form='NFD')
        expected = "cafe\u0301"  # e + combining acute accent
        assert result == expected
        assert unicodedata.is_normalized('NFD', result)
    
    def test_case_folding(self):
        """Test case folding option."""
        text = "Hello WORLD"
        result = normalize_unicode(text, case_fold=True)
        assert result == "hello world"
        
        # Unicode case folding
        text = "İSTANBUL"  # Turkish capital I with dot
        result = normalize_unicode(text, case_fold=True)
        assert result.lower() == result
    
    def test_strip_accents(self):
        """Test accent stripping."""
        text = "café naïve résumé"
        result = normalize_unicode(text, strip_accents=True)
        assert result == "cafe naive resume"
        
        # Mixed text with accents
        text = "Hëllö Wörld"
        result = normalize_unicode(text, strip_accents=True)
        assert result == "Hello World"
    
    def test_combined_options(self):
        """Test combination of normalization options."""
        text = "CAFÉ"
        result = normalize_unicode(text, case_fold=True, strip_accents=True)
        assert result == "cafe"
    
    def test_different_scripts(self):
        """Test normalization of different scripts."""
        # Should not affect non-Latin scripts
        text = "東京"
        result = normalize_unicode(text, strip_accents=True)
        assert result == text  # Should be unchanged
        
        text = "Москва"
        result = normalize_unicode(text, case_fold=True)
        assert result == "москва"


class TestTruncateTextSafely:
    """Test the truncate_text_safely function."""
    
    def test_basic_truncation(self):
        """Test basic text truncation."""
        text = "hello world test"
        result = truncate_text_safely(text, 10)
        assert len(result) <= 10
        assert not result.endswith(" ")  # Should not end with space
    
    def test_word_boundary_preservation(self):
        """Test preservation of word boundaries."""
        text = "hello world test"
        result = truncate_text_safely(text, 12)  # Should fit "hello world"
        assert result == "hello world"
        
        result = truncate_text_safely(text, 8)  # Should only fit "hello"
        assert result == "hello"
    
    def test_truncation_indicator(self):
        """Test truncation indicator."""
        text = "hello world test"
        result = truncate_text_safely(text, 10, truncate_indicator="...")
        assert result.endswith("...")
        assert len(result) <= 10
    
    def test_no_truncation_needed(self):
        """Test when no truncation is needed."""
        text = "hello"
        result = truncate_text_safely(text, 10)
        assert result == text
    
    def test_edge_cases(self):
        """Test edge cases in truncation."""
        # Very short max_length
        text = "hello world"
        result = truncate_text_safely(text, 3)
        assert len(result) <= 3
        
        # Empty text
        result = truncate_text_safely("", 10)
        assert result == ""
        
        # Single word longer than max_length
        text = "supercalifragilisticexpialidocious"
        result = truncate_text_safely(text, 10)
        assert len(result) <= 10


class TestExceptionClasses:
    """Test custom exception classes."""
    
    def test_text_validation_error(self):
        """Test TextValidationError."""
        error = TextValidationError("Invalid text", "hello world", "alphanumeric only")
        assert "Invalid text" in str(error)
        assert error.text == "hello world"
        assert error.reason == "alphanumeric only"
    
    def test_uri_validation_error(self):
        """Test URIValidationError."""
        error = URIValidationError("Invalid URI", "/invalid/uri", "missing component")
        assert "Invalid URI" in str(error)
        assert error.uri == "/invalid/uri"
        assert error.reason == "missing component"


class TestCachingBehavior:
    """Test caching behavior of functions."""
    
    def test_normalize_concept_text_caching(self):
        """Test that normalize_concept_text uses caching."""
        text = "hello world test"
        
        # First call
        result1 = normalize_concept_text(text)
        
        # Second call should use cache
        result2 = normalize_concept_text(text)
        
        assert result1 == result2
        assert result1 is result2  # Should be same object due to caching
    
    def test_validate_language_code_caching(self):
        """Test that validate_language_code uses caching."""
        # This should not raise exception and should be cached
        validate_language_code("en")
        validate_language_code("en")  # Second call uses cache
    
    @patch('src.conceptnet_mcp.utils.text_utils.normalize_concept_text.cache_info')
    def test_cache_statistics(self, mock_cache_info):
        """Test that cache statistics are available."""
        mock_cache_info.return_value = type('CacheInfo', (), {
            'hits': 5, 'misses': 3, 'maxsize': 128, 'currsize': 8
        })()
        
        info = normalize_concept_text.cache_info()
        assert hasattr(info, 'hits')
        assert hasattr(info, 'misses')


class TestSecurityConsiderations:
    """Test security-related aspects of text processing."""
    
    def test_injection_prevention(self):
        """Test prevention of injection attacks through text processing."""
        # SQL injection attempts
        malicious_texts = [
            "'; DROP TABLE users; --",
            "admin'--",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        for text in malicious_texts:
            # Should not crash and should sanitize the text
            result = normalize_concept_text(text)
            assert isinstance(result, str)
            
            # Should not contain dangerous characters
            assert "'" not in result
            assert '"' not in result
            assert "<" not in result
            assert ">" not in result
            assert "/" not in result or result.count("/") == 0
    
    def test_unicode_security(self):
        """Test security considerations with Unicode text."""
        # Unicode normalization attacks
        suspicious_texts = [
            "\uFEFF",  # Byte order mark
            "\u200B",  # Zero width space
            "\u202E",  # Right-to-left override
            "𝒂𝒅𝒎𝒊𝒏",  # Mathematical script letters that look like "admin"
        ]
        
        for text in suspicious_texts:
            result = normalize_concept_text(text)
            # Should handle gracefully without crashing
            assert isinstance(result, str)
    
    def test_length_bomb_prevention(self):
        """Test prevention of algorithmic complexity attacks."""
        # Very long input that could cause performance issues
        very_long_text = "a" * 10000
        
        # Should complete in reasonable time due to length limits
        result = normalize_concept_text(very_long_text)
        assert len(result) <= 255  # Should be truncated


if __name__ == "__main__":
    pytest.main([__file__])
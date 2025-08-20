"""
Comprehensive unit tests for the logging module.

This test suite verifies all logging components including formatters, loggers,
configuration functions, and performance monitoring capabilities.
"""

import pytest
import json
import logging
import threading
import time
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

from src.conceptnet_mcp.utils.logging import (
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
    _request_context,
)


class TestJSONFormatter:
    """Test the JSONFormatter class."""
    
    def test_format_basic_record(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test.logger"
        assert data["module"] == "path"
        assert data["line"] == 42
        assert "timestamp" in data
        assert "process_id" in data
        assert "thread_id" in data
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter(extra_fields=["custom_field"])
        record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.custom_field = "custom_value"
        record.ignored_field = "ignored"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["custom_field"] == "custom_value"
        assert "ignored_field" not in data
    
    def test_format_with_exception(self):
        """Test formatting with exception information."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="/test/path.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "ERROR"
        assert data["message"] == "Error occurred"
        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test exception" in data["exception"]
    
    def test_format_with_request_context(self):
        """Test formatting with request context."""
        formatter = JSONFormatter()
        
        # Set request context
        _request_context.request_id = "req-123"
        _request_context.user_id = "user-456"
        _request_context.operation = "test_op"
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["request_id"] == "req-123"
        assert data["user_id"] == "user-456"
        assert data["operation"] == "test_op"
        
        # Clean up
        _request_context.request_id = None
        _request_context.user_id = None
        _request_context.operation = None
    
    def test_serialize_complex_types(self):
        """Test serialization of complex data types."""
        formatter = JSONFormatter()
        
        class CustomObject:
            def __str__(self):
                return "custom_object"
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.custom_object = CustomObject()
        record.bytes_data = b"binary_data"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        # Should handle complex types gracefully
        assert isinstance(result, str)
        assert json.loads(result)  # Should be valid JSON


class TestMCPFormatter:
    """Test the MCPFormatter class."""
    
    def test_format_basic_record(self):
        """Test basic record formatting."""
        formatter = MCPFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        assert "INFO" in result
        assert "Test message" in result
        assert "test.logger" in result
        assert "path.py:42" in result
    
    def test_format_with_colors(self):
        """Test formatting with colors enabled."""
        formatter = MCPFormatter(use_colors=True)
        
        # Test different log levels
        for level, level_name in [(logging.DEBUG, "DEBUG"), 
                                 (logging.INFO, "INFO"), 
                                 (logging.WARNING, "WARNING"), 
                                 (logging.ERROR, "ERROR"), 
                                 (logging.CRITICAL, "CRITICAL")]:
            record = logging.LogRecord(
                name="test.logger",
                level=level,
                pathname="/test/path.py",
                lineno=42,
                msg=f"Test {level_name} message",
                args=(),
                exc_info=None
            )
            
            result = formatter.format(record)
            assert level_name in result
            # Colors are ANSI escape codes, so check for escape sequences
            if level >= logging.WARNING:
                assert "\033[" in result  # Should have color codes for warnings and above
    
    def test_format_with_request_context(self):
        """Test formatting with request context."""
        formatter = MCPFormatter()
        
        # Set request context
        _request_context.request_id = "req-123"
        _request_context.operation = "test_op"
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        assert "[req-123]" in result
        assert "[test_op]" in result
        
        # Clean up
        _request_context.request_id = None
        _request_context.operation = None
    
    def test_format_long_message_truncation(self):
        """Test truncation of very long messages."""
        formatter = MCPFormatter()
        long_message = "A" * 2000  # Very long message
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg=long_message,
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        # Message should be truncated and have truncation indicator
        assert len(result) < len(long_message) + 200  # Should be significantly shorter
        assert "..." in result or "[truncated]" in result.lower()


class TestRequestLogger:
    """Test the RequestLogger class."""
    
    def test_context_manager_basic(self):
        """Test basic context manager functionality."""
        logger = RequestLogger("test.logger")
        
        with logger.request_context("req-123", "test_op"):
            assert _request_context.request_id == "req-123"
            assert _request_context.operation == "test_op"
        
        # Context should be cleared after exiting
        assert _request_context.request_id is None
        assert _request_context.operation is None
    
    def test_context_manager_with_user(self):
        """Test context manager with user ID."""
        logger = RequestLogger("test.logger")
        
        with logger.request_context("req-123", "test_op", user_id="user-456"):
            assert _request_context.request_id == "req-123"
            assert _request_context.operation == "test_op"
            assert _request_context.user_id == "user-456"
        
        assert _request_context.user_id is None
    
    def test_context_manager_exception_handling(self):
        """Test that context is cleared even when exception occurs."""
        logger = RequestLogger("test.logger")
        
        try:
            with logger.request_context("req-123", "test_op"):
                assert _request_context.request_id == "req-123"
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Context should still be cleared
        assert _request_context.request_id is None
        assert _request_context.operation is None
    
    def test_log_request_start(self):
        """Test request start logging."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = RequestLogger("test.logger")
            logger.log_request_start("req-123", "GET", "/api/test", {"param": "value"})
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert "Request started" in call_args[0]
    
    def test_log_request_end(self):
        """Test request end logging."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = RequestLogger("test.logger")
            logger.log_request_end("req-123", 200, {"result": "success"}, 0.5)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert "Request completed" in call_args[0]
    
    def test_log_request_error(self):
        """Test request error logging."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = RequestLogger("test.logger")
            error = ValueError("Test error")
            logger.log_request_error("req-123", error, {"context": "test"})
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Request failed" in call_args[0][0]
            assert call_args[1]["exc_info"] is True


class TestPerformanceLogger:
    """Test the PerformanceLogger class."""
    
    def test_context_manager_basic(self):
        """Test basic performance timing."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            perf_logger = PerformanceLogger("test.logger")
            
            with perf_logger.timer("test_operation"):
                time.sleep(0.01)  # Small delay
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert "test_operation completed" in call_args[0]
    
    def test_timer_with_threshold(self):
        """Test timer with performance threshold."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            perf_logger = PerformanceLogger("test.logger")
            
            # Operation that exceeds threshold
            with perf_logger.timer("slow_operation", threshold=0.001):
                time.sleep(0.01)
            
            # Should log warning for slow operation
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0]
            assert "slow performance" in call_args[0].lower()
    
    def test_timer_with_exception(self):
        """Test timer behavior when exception occurs."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            perf_logger = PerformanceLogger("test.logger")
            
            try:
                with perf_logger.timer("failing_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Should still log the timing
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0]
            assert "failing_operation failed" in call_args[0]
    
    def test_log_performance_metrics(self):
        """Test performance metrics logging."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            perf_logger = PerformanceLogger("test.logger")
            metrics = {
                "cpu_usage": 45.2,
                "memory_usage": 78.5,
                "requests_per_second": 150.0
            }
            
            perf_logger.log_performance_metrics(metrics)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert "Performance metrics" in call_args[0]


class TestConfigurationFunctions:
    """Test logging configuration functions."""
    
    def test_configure_logging_basic(self):
        """Test basic logging configuration."""
        with patch('src.conceptnet_mcp.utils.logging.logging.basicConfig') as mock_basic_config:
            configure_logging(level="INFO")
            mock_basic_config.assert_called_once()
    
    def test_configure_logging_with_file(self):
        """Test logging configuration with file output."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            configure_logging(level="DEBUG", log_file=temp_path, log_format="json")
            
            # Test that a logger can write to the file
            logger = logging.getLogger("test_logger")
            logger.info("Test message")
            
            # Check that file exists and has content
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_configure_logging_json_format(self):
        """Test logging configuration with JSON format."""
        with patch('src.conceptnet_mcp.utils.logging.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            configure_logging(level="INFO", log_format="json")
            
            # Should configure JSON formatter
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0
    
    def test_configure_logging_human_format(self):
        """Test logging configuration with human-readable format."""
        configure_logging(level="INFO", log_format="human")
        
        # Should configure human-readable formatter
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    
    @patch('src.conceptnet_mcp.utils.logging.logging.handlers.RotatingFileHandler')
    def test_setup_production_logging(self, mock_rotating_handler):
        """Test production logging setup."""
        mock_handler = MagicMock()
        mock_rotating_handler.return_value = mock_handler
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            result = setup_production_logging(
                log_file=log_file,
                max_bytes=10*1024*1024,
                backup_count=5,
                log_format="json"
            )
            
            assert result is not None
            mock_rotating_handler.assert_called_once_with(
                log_file, maxBytes=10*1024*1024, backupCount=5
            )
    
    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        
        # Test with default name
        default_logger = get_logger()
        assert isinstance(default_logger, logging.Logger)
        assert default_logger.name == "conceptnet_mcp"


class TestConvenienceFunctions:
    """Test convenience logging functions."""
    
    def test_timed_decorator(self):
        """Test timed decorator functionality."""
        # Test that the timed decorator works
        @timed("test_operation")
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
    
    def test_global_loggers(self):
        """Test global logger instances."""
        # Test that global instances are available
        assert request_logger is not None
        assert performance_logger is not None
        assert callable(timed)


class TestThreadSafety:
    """Test thread safety of logging components."""
    
    def test_request_context_thread_safety(self):
        """Test that request context is thread-local."""
        results = []
        
        def worker(thread_id):
            logger = RequestLogger("test.logger")
            with logger.request_context(f"req-{thread_id}", f"op-{thread_id}"):
                time.sleep(0.01)  # Small delay to ensure threads overlap
                results.append({
                    'thread_id': thread_id,
                    'request_id': _request_context.request_id,
                    'operation': _request_context.operation
                })
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread should see its own context
        assert len(results) == 5
        for result in results:
            expected_request_id = f"req-{result['thread_id']}"
            expected_operation = f"op-{result['thread_id']}"
            assert result['request_id'] == expected_request_id
            assert result['operation'] == expected_operation
    
    def test_performance_logger_thread_safety(self):
        """Test that performance logging works correctly with multiple threads."""
        results = []
        
        def worker(thread_id):
            perf_logger = PerformanceLogger("test.logger")
            with patch('src.conceptnet_mcp.utils.logging.logging.getLogger'):
                with perf_logger.timer(f"operation-{thread_id}"):
                    time.sleep(0.01)
                    results.append(thread_id)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        assert set(results) == {0, 1, 2}


class TestErrorHandling:
    """Test error handling in logging components."""
    
    def test_json_formatter_handles_serialization_errors(self):
        """Test that JSON formatter handles serialization errors gracefully."""
        formatter = JSONFormatter()
        
        class NonSerializable:
            def __init__(self):
                self.circular_ref = self
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.non_serializable = NonSerializable()
        
        # Should not raise an exception
        result = formatter.format(record)
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert data["message"] == "Test message"
    
    def test_logger_handles_missing_attributes(self):
        """Test that loggers handle missing attributes gracefully."""
        formatter = MCPFormatter()
        
        # Create a record with minimal attributes
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Should not raise an exception
        result = formatter.format(record)
        assert isinstance(result, str)
        assert "Test message" in result


if __name__ == "__main__":
    pytest.main([__file__])
"""
Logging configuration and utilities for ConceptNet MCP server.

This module provides comprehensive logging setup, custom formatters, and logging utilities
specifically designed for production-ready ConceptNet MCP server operations. It follows
Python logging best practices with structured logging, performance monitoring, and
flexible configuration options.

Features:
- Production-ready structured logging with JSON format
- Multiple handlers for console, file, and error logging
- Custom formatters with MCP-specific context
- Performance metrics and request logging
- Thread-safe logging operations
- Log rotation and file management
- Configurable log levels per component
- Integration with exception handling
"""

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from contextlib import contextmanager
from functools import wraps

# Thread-local storage for request context
_request_context = threading.local()


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production environments.
    
    This formatter outputs log records as JSON objects with consistent structure,
    making logs easily parseable by log aggregation systems like ELK, Splunk, etc.
    """
    
    def __init__(
        self,
        include_mcp_context: bool = True,
        include_performance: bool = True,
        extra_fields: Optional[Dict[str, str]] = None
    ):
        super().__init__()
        self.include_mcp_context = include_mcp_context
        self.include_performance = include_performance
        self.extra_fields = extra_fields or {}
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'hostname': self.hostname
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add MCP-specific context if available
        if self.include_mcp_context:
            mcp_context = getattr(_request_context, 'context', {})
            if mcp_context:
                log_entry['mcp'] = mcp_context
        
        # Add performance metrics if enabled
        if self.include_performance:
            performance = getattr(_request_context, 'performance', {})
            if performance:
                log_entry['performance'] = performance
        
        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        # Add configured extra fields
        for field_name, field_value in self.extra_fields.items():
            log_entry[field_name] = field_value
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))


class MCPFormatter(logging.Formatter):
    """
    Human-readable formatter for MCP server operations.
    
    This formatter provides enhanced log messages with MCP-specific context
    and color coding for different log levels (when supported).
    """
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(
        self,
        include_colors: bool = True,
        include_mcp_context: bool = True,
        format_string: Optional[str] = None,
        use_colors: bool = None
    ):
        # Handle backward compatibility
        if use_colors is not None:
            include_colors = use_colors
        if format_string is None:
            format_string = (
                '%(asctime)s | %(levelname)-8s | %(name)-20s | '
                '%(funcName)s:%(lineno)d | %(message)s'
            )
        super().__init__(format_string)
        self.include_colors = include_colors and self._supports_color()
        self.include_mcp_context = include_mcp_context
    
    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        return (
            hasattr(sys.stderr, 'isatty') and sys.stderr.isatty() and
            os.environ.get('TERM') != 'dumb'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors and MCP context.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Add MCP context to the message if available
        if self.include_mcp_context:
            mcp_context = getattr(_request_context, 'context', {})
            if mcp_context:
                tool_name = mcp_context.get('tool_name')
                request_id = mcp_context.get('request_id')
                if tool_name or request_id:
                    context_parts = []
                    if tool_name:
                        context_parts.append(f"tool={tool_name}")
                    if request_id:
                        context_parts.append(f"req={request_id[:8]}")  # Short request ID
                    record.msg = f"[{','.join(context_parts)}] {record.msg}"
        
        # Format the base message
        formatted = super().format(record)
        
        # Add colors if supported
        if self.include_colors:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted


class PerformanceLogger:
    """
    Utility for logging performance metrics and timing information.
    
    This class provides context managers and decorators for measuring
    execution time and logging performance metrics.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    @contextmanager
    def measure_time(self, operation: str, **context):
        """
        Context manager for measuring operation execution time.
        
        Args:
            operation: Name of the operation being measured
            **context: Additional context to include in logs
            
        Yields:
            Dictionary containing timing information
        """
        start_time = time.perf_counter()
        timing_info = {'operation': operation, 'start_time': start_time}
        
        try:
            yield timing_info
            success = True
        except Exception as e:
            success = False
            timing_info['error'] = str(e)
            raise
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            timing_info.update({
                'end_time': end_time,
                'duration_seconds': duration,
                'duration_ms': duration * 1000,
                'success': success
            })
            
            # Store performance data in thread-local storage
            if not hasattr(_request_context, 'performance'):
                _request_context.performance = {}
            _request_context.performance[operation] = timing_info
            
            # Log performance metrics
            log_level = logging.INFO if success else logging.WARNING
            self.logger.log(
                log_level,
                f"Operation '{operation}' completed in {duration*1000:.2f}ms",
                extra={
                    'performance_operation': operation,
                    'performance_duration_ms': duration * 1000,
                    'performance_success': success,
                    **context
                }
            )
    
    def timed_operation(self, operation_name: Optional[str] = None):
        """
        Decorator for timing function execution.
        
        Args:
            operation_name: Name for the operation (defaults to function name)
            
        Returns:
            Decorator function
        """
        def decorator(func):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure_time(op_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def timer(self, operation: str):
        """
        Context manager for timing operations.
        
        Args:
            operation: Name of the operation being timed
            
        Returns:
            Context manager that measures execution time
        """
        return self.measure_time(operation)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """
        Log performance metrics.
        
        Args:
            metrics: Dictionary of performance metrics to log
        """
        self.logger.info(
            "Performance metrics recorded",
            extra={
                'performance_metrics': metrics,
                'metrics_count': len(metrics)
            }
        )


class RequestLogger:
    """
    Enhanced request logger for MCP operations with structured logging.
    
    This class provides comprehensive logging for MCP tool invocations,
    API requests, and error handling with proper context management.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("requests")
        self.performance_logger = PerformanceLogger(self.logger)
    
    def set_request_context(
        self,
        request_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        **context
    ):
        """
        Set MCP request context for current thread.
        
        Args:
            request_id: Unique request identifier
            tool_name: Name of the MCP tool being executed
            user_id: User identifier (if available)
            **context: Additional context information
        """
        if not hasattr(_request_context, 'context'):
            _request_context.context = {}
        
        _request_context.context.update({
            'request_id': request_id,
            'tool_name': tool_name,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            **context
        })
    
    def clear_request_context(self):
        """Clear the request context for current thread."""
        if hasattr(_request_context, 'context'):
            delattr(_request_context, 'context')
        if hasattr(_request_context, 'performance'):
            delattr(_request_context, 'performance')
    
    @contextmanager
    def request_context(self, request_id: str, operation: str, **kwargs):
        """
        Context manager for setting request context.
        
        Args:
            request_id: Unique request identifier
            operation: Operation being performed
            **kwargs: Additional context information
        """
        self.set_request_context(request_id=request_id, tool_name=operation, **kwargs)
        try:
            yield
        finally:
            self.clear_request_context()
    
    def log_request_start(self, request_id: str, operation: str, parameters: Optional[Dict] = None):
        """
        Log the start of a request.
        
        Args:
            request_id: Unique request identifier
            operation: Operation being started
            parameters: Request parameters
        """
        self.logger.info(
            f"Request started: {operation}",
            extra={
                'request_id': request_id,
                'operation': operation,
                'parameters': parameters or {},
                'request_phase': 'start'
            }
        )
    
    def log_request_end(self, request_id: str, operation: str, success: bool = True,
                       duration: Optional[float] = None):
        """
        Log the end of a request.
        
        Args:
            request_id: Unique request identifier
            operation: Operation that ended
            success: Whether the operation was successful
            duration: Duration in seconds
        """
        log_level = logging.INFO if success else logging.WARNING
        message = f"Request {'completed' if success else 'failed'}: {operation}"
        
        extra_data = {
            'request_id': request_id,
            'operation': operation,
            'success': success,
            'request_phase': 'end'
        }
        
        if duration is not None:
            extra_data['duration_seconds'] = duration
            extra_data['duration_ms'] = duration * 1000
            message += f" in {duration*1000:.2f}ms"
        
        self.logger.log(log_level, message, extra=extra_data)
    
    def log_request_error(self, request_id: str, operation: str, error: Exception,
                         duration: Optional[float] = None):
        """
        Log a request error.
        
        Args:
            request_id: Unique request identifier
            operation: Operation that failed
            error: Exception that occurred
            duration: Duration before failure
        """
        message = f"Request failed: {operation} - {str(error)}"
        
        extra_data = {
            'request_id': request_id,
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_phase': 'error'
        }
        
        if duration is not None:
            extra_data['duration_seconds'] = duration
            extra_data['duration_ms'] = duration * 1000
        
        self.logger.error(message, extra=extra_data, exc_info=True)
    
    def log_tool_invocation(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        execution_time: Optional[float] = None,
        success: bool = True,
        error: Optional[Exception] = None
    ):
        """
        Log MCP tool invocation with parameters and results.
        
        Args:
            tool_name: Name of the invoked tool
            parameters: Tool parameters
            execution_time: Execution time in seconds
            success: Whether the tool execution was successful
            error: Error that occurred (if any)
        """
        log_level = logging.INFO if success else logging.ERROR
        message = f"MCP tool '{tool_name}' {'completed' if success else 'failed'}"
        
        if execution_time is not None:
            message += f" in {execution_time*1000:.2f}ms"
        
        extra_data = {
            'mcp_tool_name': tool_name,
            'mcp_tool_success': success,
            'mcp_tool_parameters': parameters,
            'mcp_tool_parameter_count': len(parameters)
        }
        
        if execution_time is not None:
            extra_data['mcp_tool_execution_time_ms'] = execution_time * 1000
        
        if error:
            extra_data['mcp_tool_error'] = str(error)
            extra_data['mcp_tool_error_type'] = type(error).__name__
        
        self.logger.log(log_level, message, extra=extra_data)
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """
        Log ConceptNet API request with performance metrics.
        
        Args:
            endpoint: API endpoint called
            method: HTTP method used
            response_time: Response time in seconds
            status_code: HTTP status code
            request_size: Request payload size in bytes
            response_size: Response payload size in bytes
        """
        log_level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
        message = f"API {method} {endpoint} -> {status_code} ({response_time*1000:.2f}ms)"
        
        extra_data = {
            'api_endpoint': endpoint,
            'api_method': method,
            'api_status_code': status_code,
            'api_response_time_ms': response_time * 1000,
            'api_success': 200 <= status_code < 400
        }
        
        if request_size is not None:
            extra_data['api_request_size_bytes'] = request_size
        if response_size is not None:
            extra_data['api_response_size_bytes'] = response_size
        
        self.logger.log(log_level, message, extra=extra_data)
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: int = logging.ERROR
    ):
        """
        Log error with comprehensive context information.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            level: Log level to use
        """
        message = f"Error occurred: {str(error)}"
        
        extra_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_context': context or {}
        }
        
        # Add custom exception attributes if available
        if hasattr(error, 'error_code'):
            extra_data['error_code'] = error.error_code.name if hasattr(error.error_code, 'name') else str(error.error_code)
        if hasattr(error, 'details'):
            extra_data['error_details'] = error.details
        if hasattr(error, 'suggestions'):
            extra_data['error_suggestions'] = error.suggestions
        
        self.logger.log(level, message, extra=extra_data, exc_info=True)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance with the given name.
    
    Args:
        name: Logger name (typically module name)
        level: Optional logging level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"conceptnet_mcp.{name}")
    
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger


def configure_logging(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_structured: bool = False,
    enable_file_rotation: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    force: bool = False,
    log_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure comprehensive logging for the ConceptNet MCP server.
    
    This function sets up production-ready logging with multiple handlers,
    structured logging options, and proper error handling.
    
    Args:
        level: Root logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        enable_console: Whether to enable console logging
        enable_structured: Whether to use structured/JSON logging
        enable_file_rotation: Whether to enable log file rotation
        max_file_size: Maximum size for log files before rotation
        backup_count: Number of backup files to keep
        force: Whether to force reconfiguration of existing loggers
        log_format: Custom log format string
        
    Returns:
        Dictionary containing the logging configuration used
    """
    # Use basic logging configuration if simple setup is requested
    if log_format and not log_file and not enable_structured:
        import logging
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=log_format,
            force=force
        )
        return {'format': log_format, 'level': level}
    # Build logging configuration dictionary
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'class': 'logging.Formatter',
                'format': '%(levelname)-8s | %(name)-15s | %(message)s'
            }
        },
        'handlers': {},
        'loggers': {
            'conceptnet_mcp': {
                'level': level.upper(),
                'handlers': [],
                'propagate': False
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': []
        }
    }
    
    # Add custom formatters based on configuration
    if enable_structured:
        config['formatters']['json'] = {
            '()': JSONFormatter,
            'include_mcp_context': True,
            'include_performance': True
        }
    
    config['formatters']['mcp'] = {
        '()': MCPFormatter,
        'include_colors': True,
        'include_mcp_context': True
    }
    
    # Console handler
    if enable_console:
        console_formatter = 'json' if enable_structured else 'mcp'
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': level.upper(),
            'formatter': console_formatter,
            'stream': 'ext://sys.stdout'
        }
        config['loggers']['conceptnet_mcp']['handlers'].append('console')
    
    # Error console handler (always uses standard formatter)
    config['handlers']['error_console'] = {
        'class': 'logging.StreamHandler',
        'level': 'ERROR',
        'formatter': 'detailed',
        'stream': 'ext://sys.stderr'
    }
    config['loggers']['conceptnet_mcp']['handlers'].append('error_console')
    
    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if enable_file_rotation:
            config['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'json' if enable_structured else 'detailed',
                'filename': str(log_file),
                'maxBytes': max_file_size,
                'backupCount': backup_count,
                'encoding': 'utf-8'
            }
        else:
            config['handlers']['file'] = {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'json' if enable_structured else 'detailed',
                'filename': str(log_file),
                'mode': 'a',
                'encoding': 'utf-8'
            }
        
        config['loggers']['conceptnet_mcp']['handlers'].append('file')
        
        # Separate error file
        error_file = log_file.parent / f"{log_file.stem}_errors{log_file.suffix}"
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler' if enable_file_rotation else 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'json' if enable_structured else 'detailed',
            'filename': str(error_file),
            'encoding': 'utf-8'
        }
        
        if enable_file_rotation:
            config['handlers']['error_file'].update({
                'maxBytes': max_file_size,
                'backupCount': backup_count
            })
        else:
            config['handlers']['error_file']['mode'] = 'a'
        
        config['loggers']['conceptnet_mcp']['handlers'].append('error_file')
    
    # Configure third-party loggers
    config['loggers'].update({
        'urllib3': {'level': 'WARNING', 'propagate': True},
        'requests': {'level': 'WARNING', 'propagate': True},
        'httpx': {'level': 'WARNING', 'propagate': True},
        'asyncio': {'level': 'WARNING', 'propagate': True}
    })
    
    # Apply configuration
    if force:
        # Clear existing handlers
        for logger_name in logging.Logger.manager.loggerDict:
            if logger_name.startswith('conceptnet_mcp'):
                logger = logging.getLogger(logger_name)
                logger.handlers.clear()
    
    logging.config.dictConfig(config)
    
    return config


def setup_development_logging():
    """Set up logging optimized for development with colorized console output."""
    return configure_logging(
        level="DEBUG",
        enable_console=True,
        enable_structured=False,
        log_file=None
    )


def setup_production_logging(log_file: Union[str, Path], max_bytes: int = 10 * 1024 * 1024,
                           backup_count: int = 5):
    """Set up logging optimized for production with structured JSON output."""
    return configure_logging(
        level="INFO",
        log_file=log_file,
        enable_console=True,
        enable_structured=True,
        enable_file_rotation=True,
        max_file_size=max_bytes,
        backup_count=backup_count
    )


# Global performance logger instance
performance_logger = PerformanceLogger()

# Convenience decorators
timed = performance_logger.timed_operation

# Module-level request logger
request_logger = RequestLogger()
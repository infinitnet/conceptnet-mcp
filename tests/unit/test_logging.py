"""Unit tests for conceptnet_mcp.utils.logging."""

import json
import logging
import threading

import pytest

from conceptnet_mcp.utils.logging import (
    JSONFormatter,
    MCPFormatter,
    PerformanceLogger,
    RequestLogger,
    configure_logging,
    get_logger,
    setup_development_logging,
    setup_production_logging,
)


def make_record(message="Test message", level=logging.INFO, exc_info=None, **extra):
    record = logging.LogRecord(
        "test.logger", level, "/tmp/mod.py", 42, message, (), exc_info
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


@pytest.fixture(autouse=True)
def reset_logging_state():
    yield
    package_logger = logging.getLogger("conceptnet_mcp")
    for handler in list(package_logger.handlers):
        handler.close()
        package_logger.removeHandler(handler)
    RequestLogger().clear_request_context()


class TestJSONFormatter:
    def test_basic_record(self):
        data = json.loads(JSONFormatter().format(make_record()))
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["line"] == 42
        assert "timestamp" in data and "hostname" in data

    def test_exception(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = make_record(level=logging.ERROR, exc_info=sys.exc_info())
        data = json.loads(JSONFormatter().format(record))
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "boom"

    def test_extra_fields(self):
        record = make_record(request_id="req-1")
        formatter = JSONFormatter(extra_fields={"service": "conceptnet"})
        data = json.loads(formatter.format(record))
        assert data["request_id"] == "req-1"
        assert data["service"] == "conceptnet"

    def test_non_serializable_extra_does_not_raise(self):
        class Custom:
            def __str__(self):
                return "custom-object"

        data = json.loads(JSONFormatter().format(make_record(obj=Custom())))
        assert data["obj"] == "custom-object"

    def test_request_context_included(self):
        request_logger = RequestLogger()
        with request_logger.request_context(request_id="req-123", tool_name="concept_lookup"):
            data = json.loads(JSONFormatter().format(make_record()))
        assert data["mcp"]["request_id"] == "req-123"
        assert data["mcp"]["tool_name"] == "concept_lookup"


class TestMCPFormatter:
    def test_basic_record(self):
        output = MCPFormatter(include_colors=False).format(make_record())
        assert "Test message" in output
        assert "INFO" in output

    def test_context_prefix(self):
        request_logger = RequestLogger()
        with request_logger.request_context(request_id="req-12345678", tool_name="concept_query"):
            output = MCPFormatter(include_colors=False).format(make_record())
        assert "tool=concept_query" in output
        assert "req=req-1234" in output


class TestRequestLogger:
    def test_context_is_set_and_cleared(self):
        request_logger = RequestLogger()
        with request_logger.request_context(request_id="r1", tool_name="t1", user_id="u1"):
            data = json.loads(JSONFormatter().format(make_record()))
            assert data["mcp"]["user_id"] == "u1"
        data = json.loads(JSONFormatter().format(make_record()))
        assert "mcp" not in data

    def test_context_cleared_on_exception(self):
        request_logger = RequestLogger()
        with pytest.raises(RuntimeError):
            with request_logger.request_context(request_id="r1", tool_name="t1"):
                raise RuntimeError("fail")
        assert "mcp" not in json.loads(JSONFormatter().format(make_record()))

    def test_requires_identifier(self):
        with pytest.raises(ValueError):
            with RequestLogger().request_context():
                pass

    def test_request_start_and_end_are_logged(self, caplog):
        request_logger = RequestLogger(logger_name="test_requests")
        request_logger.logger.propagate = True
        with caplog.at_level(logging.INFO):
            request_logger.log_request_start("r1", "lookup", {"term": "dog"})
            request_logger.log_request_end("r1", "lookup", success=True)
        messages = [r.getMessage() for r in caplog.records]
        assert any("Request started: lookup" in m for m in messages)
        assert len(messages) >= 2


class TestPerformanceLogger:
    def test_measure_time_records_duration(self):
        perf = PerformanceLogger(logging.getLogger("test.perf"))
        with perf.measure_time("op") as info:
            pass
        assert info["success"] is True
        assert info["duration_ms"] >= 0

    def test_measure_time_records_failure(self):
        perf = PerformanceLogger(logging.getLogger("test.perf"))
        with pytest.raises(ValueError):
            with perf.measure_time("op") as info:
                raise ValueError("bad")
        assert info["success"] is False
        assert info["error"] == "bad"

    def test_timed_operation_decorator(self):
        perf = PerformanceLogger(logging.getLogger("test.perf"))

        @perf.timed_operation("decorated")
        def work():
            return 7

        assert work() == 7


class TestConfiguration:
    def test_get_logger_prefix(self):
        assert get_logger("test.module").name == "conceptnet_mcp.test.module"

    def test_get_logger_level(self):
        assert get_logger("lvl", level="debug").level == logging.DEBUG

    def test_configure_logging_with_file(self, tmp_path):
        log_file = tmp_path / "logs" / "app.log"
        config = configure_logging(level="INFO", log_file=log_file)
        get_logger("file_test").info("hello file")
        for handler in logging.getLogger("conceptnet_mcp").handlers:
            handler.flush()
        assert "file" in config["handlers"]
        assert "hello file" in log_file.read_text(encoding="utf-8")

    def test_console_handlers_use_stderr(self):
        config = configure_logging(level="INFO")
        assert config["handlers"]["console"]["stream"] == "ext://sys.stderr"

    def test_setup_production_logging_is_json(self, tmp_path):
        log_file = tmp_path / "prod.log"
        setup_production_logging(log_file)
        get_logger("prod_test").info("structured")
        for handler in logging.getLogger("conceptnet_mcp").handlers:
            handler.flush()
        line = log_file.read_text(encoding="utf-8").strip().splitlines()[-1]
        assert json.loads(line)["message"] == "structured"

    def test_setup_development_logging(self):
        assert setup_development_logging()["loggers"]["conceptnet_mcp"]["level"] == "DEBUG"


class TestThreadSafety:
    def test_context_is_thread_local(self):
        request_logger = RequestLogger()
        seen = {}

        def worker():
            seen["mcp"] = "mcp" in json.loads(JSONFormatter().format(make_record()))

        with request_logger.request_context(request_id="main", tool_name="t"):
            thread = threading.Thread(target=worker)
            thread.start()
            thread.join()
        assert seen["mcp"] is False

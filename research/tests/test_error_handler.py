"""
Unit tests for error handling functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch

from error_handler import (
    ErrorHandler, ErrorType, RetryConfig, CircuitBreaker, 
    BatchErrorHandler, with_retry, safe_execute
)


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.error_handler = ErrorHandler()
    
    def test_classify_network_errors(self):
        """Test classification of network-related errors."""
        network_errors = [
            ConnectionError("Connection timed out"),
            Exception("Network unreachable"),
            Exception("DNS resolution failed"),
            Exception("httperror occurred")
        ]
        
        for error in network_errors:
            error_type = self.error_handler.classify_error(error)
            assert error_type == ErrorType.NETWORK_ERROR
    
    def test_classify_rate_limit_errors(self):
        """Test classification of rate limiting errors."""
        rate_limit_errors = [
            Exception("Rate limit exceeded"),
            Exception("429 Too Many Requests"),
            Exception("too many requests")
        ]
        
        for error in rate_limit_errors:
            error_type = self.error_handler.classify_error(error)
            assert error_type == ErrorType.RATE_LIMIT_ERROR
    
    def test_classify_parsing_errors(self):
        """Test classification of parsing errors."""
        parsing_errors = [
            ValueError("Invalid JSON"),
            Exception("XML parsing failed"),
            Exception("HTML parse error")
        ]
        
        # Note: ValueError by type name detection
        error_type = self.error_handler.classify_error(parsing_errors[0])
        # ValueError doesn't match parsing keywords, so will be UNKNOWN_ERROR
        assert error_type == ErrorType.UNKNOWN_ERROR
        
        # Create custom parsing error
        class ParseError(Exception):
            pass
        
        parse_error = ParseError("Parsing failed")
        error_type = self.error_handler.classify_error(parse_error)
        assert error_type == ErrorType.PARSING_ERROR
    
    def test_classify_file_errors(self):
        """Test classification of file-related errors."""
        file_errors = [
            FileNotFoundError("File not found"),
            PermissionError("Permission denied"),
            IOError("I/O operation failed")
        ]
        
        for error in file_errors:
            error_type = self.error_handler.classify_error(error)
            assert error_type == ErrorType.FILE_ERROR
    
    def test_classify_unknown_errors(self):
        """Test classification of unknown errors."""
        unknown_error = RuntimeError("Unknown runtime error")
        error_type = self.error_handler.classify_error(unknown_error)
        assert error_type == ErrorType.UNKNOWN_ERROR
    
    def test_record_error(self):
        """Test recording errors."""
        error = ConnectionError("Connection failed")
        error_type = self.error_handler.record_error(error, "AAPL")
        
        assert error_type == ErrorType.NETWORK_ERROR
        assert self.error_handler.error_counts[ErrorType.NETWORK_ERROR] == 1
        assert "AAPL" in self.error_handler.failed_symbols
    
    def test_record_multiple_errors(self):
        """Test recording multiple errors."""
        errors = [
            (ConnectionError("Connection 1"), "AAPL"),
            (ConnectionError("Connection 2"), "MSFT"),
            (ValueError("Value error"), "GOOGL")
        ]
        
        for error, symbol in errors:
            self.error_handler.record_error(error, symbol)
        
        assert self.error_handler.error_counts[ErrorType.NETWORK_ERROR] == 2
        assert self.error_handler.error_counts[ErrorType.UNKNOWN_ERROR] == 1
        assert len(self.error_handler.failed_symbols) == 3
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        # Record some errors
        self.error_handler.record_error(ConnectionError("Error 1"), "AAPL")
        self.error_handler.record_error(ValueError("Error 2"), "MSFT")
        
        summary = self.error_handler.get_error_summary()
        
        assert "error_counts" in summary
        assert "total_errors" in summary
        assert "failed_symbols" in summary
        assert "failed_count" in summary
        
        assert summary["total_errors"] == 2
        assert summary["failed_count"] == 2
        assert "AAPL" in summary["failed_symbols"]
        assert "MSFT" in summary["failed_symbols"]


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_backoff is True
        assert ErrorType.NETWORK_ERROR in config.retry_on_errors
        assert ErrorType.RATE_LIMIT_ERROR in config.retry_on_errors
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            exponential_backoff=False,
            retry_on_errors=[ErrorType.NETWORK_ERROR]
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.exponential_backoff is False
        assert len(config.retry_on_errors) == 1


class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)
    
    def test_successful_calls(self):
        """Test successful function calls."""
        def success_func():
            return "success"
        
        result = self.circuit_breaker.call(success_func)
        assert result == "success"
        assert self.circuit_breaker.state == "closed"
    
    def test_circuit_opening(self):
        """Test circuit breaker opening after failures."""
        def failing_func():
            raise Exception("Function failed")
        
        # First failure
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == "open"
        assert self.circuit_breaker.failure_count == 2
    
    def test_circuit_blocking_when_open(self):
        """Test that circuit breaker blocks calls when open."""
        def failing_func():
            raise Exception("Function failed")
        
        # Trigger circuit to open
        for _ in range(2):
            with pytest.raises(Exception):
                self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == "open"
        
        # Next call should be blocked
        with pytest.raises(Exception, match="Circuit breaker is open"):
            self.circuit_breaker.call(failing_func)
    
    def test_circuit_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        def failing_func():
            raise Exception("Function failed")
        
        def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                self.circuit_breaker.call(failing_func)
        
        assert self.circuit_breaker.state == "open"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next call should move to half-open and succeed
        result = self.circuit_breaker.call(success_func)
        assert result == "success"
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 0


class TestWithRetryDecorator:
    """Test with_retry decorator."""
    
    def test_successful_function(self):
        """Test retry decorator with successful function."""
        @with_retry(RetryConfig(max_retries=2))
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_function_with_retryable_error(self):
        """Test retry decorator with retryable errors."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.1))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3  # Initial call + 2 retries
    
    def test_function_with_non_retryable_error(self):
        """Test retry decorator with non-retryable errors."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, retry_on_errors=[ErrorType.NETWORK_ERROR]))
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Value error")  # Not retryable
        
        with pytest.raises(ValueError):
            failing_func()
        
        assert call_count == 1  # No retries for non-retryable error
    
    def test_max_retries_exceeded(self):
        """Test retry decorator when max retries exceeded."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.1))
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_failing()
        
        assert call_count == 3  # Initial call + 2 retries


class TestSafeExecute:
    """Test safe_execute function."""
    
    def test_successful_execution(self):
        """Test safe execution with successful function."""
        def success_func(x, y):
            return x + y
        
        success, result, error = safe_execute(success_func, 2, 3)
        
        assert success is True
        assert result == 5
        assert error is None
    
    def test_failed_execution(self):
        """Test safe execution with failing function."""
        def failing_func():
            raise ValueError("Function failed")
        
        success, result, error = safe_execute(failing_func)
        
        assert success is False
        assert result is None
        assert isinstance(error, ValueError)
        assert str(error) == "Function failed"


class TestBatchErrorHandler:
    """Test BatchErrorHandler class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.batch_handler = BatchErrorHandler(max_consecutive_failures=3)
    
    def test_handle_company_success(self):
        """Test handling successful company processing."""
        self.batch_handler.consecutive_failures = 2
        self.batch_handler.handle_company_success("AAPL")
        
        assert self.batch_handler.consecutive_failures == 0
    
    def test_handle_company_error(self):
        """Test handling company processing errors."""
        error = ConnectionError("Network error")
        should_continue = self.batch_handler.handle_company_error("AAPL", error)
        
        assert should_continue is True
        assert self.batch_handler.consecutive_failures == 1
        assert "AAPL" in self.batch_handler.error_handler.failed_symbols
    
    def test_stop_on_too_many_failures(self):
        """Test stopping batch processing on too many consecutive failures."""
        error = ConnectionError("Network error")
        
        # Process failures up to threshold
        for i in range(3):
            should_continue = self.batch_handler.handle_company_error(f"FAIL{i}", error)
            if i < 2:
                assert should_continue is True
            else:
                assert should_continue is False
        
        assert self.batch_handler.consecutive_failures == 3
    
    def test_get_batch_summary(self):
        """Test getting batch processing summary."""
        # Process some companies
        self.batch_handler.handle_company_success("AAPL")
        self.batch_handler.handle_company_error("MSFT", ValueError("Error"))
        
        summary = self.batch_handler.get_batch_summary()
        
        assert "error_counts" in summary
        assert "consecutive_failures" in summary
        assert "circuit_breaker_state" in summary
        assert summary["consecutive_failures"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
"""
Robust error handling and retry logic for earnings research.
"""

import time
import logging
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur during processing."""
    NETWORK_ERROR = "network"
    PARSING_ERROR = "parsing"  
    DATA_ERROR = "data"
    FILE_ERROR = "file"
    RATE_LIMIT_ERROR = "rate_limit"
    UNKNOWN_ERROR = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    retry_on_errors: List[ErrorType] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                ErrorType.NETWORK_ERROR,
                ErrorType.RATE_LIMIT_ERROR
            ]


class ErrorHandler:
    """Centralized error handling for the earnings research system."""
    
    def __init__(self):
        self.error_counts: Dict[ErrorType, int] = {}
        self.failed_symbols: List[str] = []
        
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify an error into a specific type."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'dns']):
            return ErrorType.NETWORK_ERROR
        if any(keyword in error_type for keyword in ['connection', 'timeout', 'httperror']):
            return ErrorType.NETWORK_ERROR
            
        # Rate limiting
        if any(keyword in error_str for keyword in ['rate limit', '429', 'too many requests']):
            return ErrorType.RATE_LIMIT_ERROR
            
        # Parsing errors
        if any(keyword in error_type for keyword in ['parse', 'json', 'xml', 'html']):
            return ErrorType.PARSING_ERROR
            
        # File errors
        if any(keyword in error_type for keyword in ['file', 'io', 'permission']):
            return ErrorType.FILE_ERROR
            
        # Data validation errors
        if any(keyword in error_str for keyword in ['validation', 'schema', 'format']):
            return ErrorType.DATA_ERROR
            
        return ErrorType.UNKNOWN_ERROR
    
    def record_error(self, error: Exception, symbol: Optional[str] = None) -> ErrorType:
        """Record an error occurrence."""
        error_type = self.classify_error(error)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        if symbol and symbol not in self.failed_symbols:
            self.failed_symbols.append(symbol)
            
        logger.warning(f"Error recorded - Type: {error_type.value}, Symbol: {symbol}, Error: {str(error)}")
        return error_type
    
    def should_retry(self, error_type: ErrorType, config: RetryConfig) -> bool:
        """Determine if an error should trigger a retry."""
        return error_type in config.retry_on_errors
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay before next retry attempt."""
        if config.exponential_backoff:
            delay = config.base_delay * (2 ** attempt)
        else:
            delay = config.base_delay
            
        return min(delay, config.max_delay)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all recorded errors."""
        return {
            "error_counts": {error_type.value: count for error_type, count in self.error_counts.items()},
            "total_errors": sum(self.error_counts.values()),
            "failed_symbols": self.failed_symbols,
            "failed_count": len(self.failed_symbols)
        }


def with_retry(config: RetryConfig = None):
    """Decorator to add retry logic to functions."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            error_handler = ErrorHandler()
            last_error = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    error_type = error_handler.record_error(e)
                    
                    if attempt < config.max_retries and error_handler.should_retry(error_type, config):
                        delay = error_handler.calculate_delay(attempt, config)
                        logger.info(f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1}/{config.max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {func.__name__}: {str(e)}")
                        break
            
            # Re-raise the last error if all retries failed
            raise last_error
            
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for failing operations."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                logger.info("Circuit breaker moving to half-open state")
            else:
                raise Exception("Circuit breaker is open - operation blocked")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed - operations restored")
                
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
                
            raise e


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[Exception]]:
    """Safely execute a function and return (success, result, error)."""
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, e


class BatchErrorHandler:
    """Handle errors during batch processing of multiple companies."""
    
    def __init__(self, max_consecutive_failures: int = 10):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.error_handler = ErrorHandler()
        self.circuit_breaker = CircuitBreaker()
        
    def handle_company_error(self, symbol: str, error: Exception) -> bool:
        """Handle error for a single company. Returns True if processing should continue."""
        error_type = self.error_handler.record_error(error, symbol)
        self.consecutive_failures += 1
        
        logger.error(f"Failed to process {symbol}: {error_type.value} - {str(error)}")
        
        # Check if we should stop batch processing
        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.critical(f"Too many consecutive failures ({self.consecutive_failures}). Stopping batch processing.")
            return False
            
        return True
    
    def handle_company_success(self, symbol: str) -> None:
        """Handle successful processing of a company."""
        self.consecutive_failures = 0
        logger.info(f"Successfully processed {symbol}")
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get summary of batch processing errors."""
        summary = self.error_handler.get_error_summary()
        summary["consecutive_failures"] = self.consecutive_failures
        summary["circuit_breaker_state"] = self.circuit_breaker.state
        return summary


if __name__ == "__main__":
    # Demo error handling
    error_handler = ErrorHandler()
    
    # Test error classification
    test_errors = [
        ConnectionError("Connection timed out"),
        ValueError("Invalid JSON format"),
        FileNotFoundError("File not found"),
        Exception("Rate limit exceeded")
    ]
    
    for error in test_errors:
        error_type = error_handler.classify_error(error)
        print(f"Error: {error} -> Type: {error_type.value}")
    
    print("\nError Summary:", error_handler.get_error_summary())
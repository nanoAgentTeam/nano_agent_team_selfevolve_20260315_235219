"""
Agent Recovery Strategies

Provides strategies for recovering from diagnosed issues.
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Dict, List


logger = logging.getLogger(__name__)


class RecoveryStrategy(ABC):
    """Base class for recovery strategies"""
    
    @abstractmethod
    def execute(self, operation: Callable[[], Any], **kwargs) -> Any:
        """
        Execute the recovery strategy.
        
        Args:
            operation: The operation to recover
            **kwargs: Strategy-specific parameters
        
        Returns:
            Result of the operation
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the strategy"""
        pass


class RetryStrategy(RecoveryStrategy):
    """
    Retry strategy for transient failures.
    
    Retries a failed operation with configurable attempts and delay.
    """
    
    def __init__(self, max_retries: int = 3, delay_seconds: float = 1.0,
                 exponential_backoff: bool = False):
        """
        Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay_seconds: Base delay between retries
            exponential_backoff: If True, delay doubles each retry
        """
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.exponential_backoff = exponential_backoff
    
    def execute(self, operation: Callable[[], Any], **kwargs) -> Any:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Callable to execute
            **kwargs: Unused (for compatibility)
        
        Returns:
            Result of successful operation
        
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        delay = self.delay_seconds
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(delay)
                    if self.exponential_backoff:
                        delay *= 2
        
        raise last_exception
    
    def get_description(self) -> str:
        return f"Retry up to {self.max_retries} times with {self.delay_seconds}s delay"


class FallbackStrategy(RecoveryStrategy):
    """
    Fallback strategy for handling failures.
    
    Executes a fallback operation when the primary fails.
    """
    
    def __init__(self, primary: Callable[[], Any], fallback: Callable[[], Any],
                 fallback_value: Any = None):
        """
        Initialize fallback strategy.
        
        Args:
            primary: Primary operation to attempt
            fallback: Fallback operation if primary fails
            fallback_value: Optional static fallback value
        """
        self.primary = primary
        self.fallback = fallback
        self.fallback_value = fallback_value
    
    def execute(self, **kwargs) -> Any:
        """
        Execute primary, fall back on failure.
        
        Args:
            **kwargs: Unused (for compatibility)
        
        Returns:
            Result from primary or fallback
        """
        try:
            return self.primary()
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            
            if self.fallback_value is not None:
                return self.fallback_value
            
            return self.fallback()
    
    def get_description(self) -> str:
        return "Execute fallback on primary failure"


class CircuitBreakerStrategy(RecoveryStrategy):
    """
    Circuit breaker strategy for repeated failures.
    
    Opens circuit after consecutive failures, preventing further attempts
    until a cooldown period passes.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
    
    def execute(self, operation: Callable[[], Any], **kwargs) -> Any:
        """
        Execute with circuit breaker protection.
        
        Args:
            operation: Callable to execute
            **kwargs: Unused
        
        Returns:
            Result of operation
        
        Raises:
            Exception: If circuit is open or operation fails
        """
        if self.is_open:
            if self._should_attempt_recovery():
                self.is_open = False
                self.failure_count = 0
                logger.info("Circuit breaker closed, attempting recovery")
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = operation()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def get_description(self) -> str:
        return f"Circuit breaker (threshold={self.failure_threshold}, timeout={self.recovery_timeout}s)"


class RecoveryManager:
    """
    Manager for recovery strategies.
    
    Registers, retrieves, and executes recovery strategies.
    """
    
    def __init__(self):
        """Initialize recovery manager"""
        self._strategies: Dict[str, RecoveryStrategy] = {}
    
    def register_strategy(self, name: str, strategy: RecoveryStrategy) -> None:
        """
        Register a recovery strategy.
        
        Args:
            name: Unique identifier for the strategy
            strategy: Strategy instance to register
        """
        self._strategies[name] = strategy
        logger.info(f"Registered recovery strategy: {name}")
    
    def get_strategy(self, name: str) -> Optional[RecoveryStrategy]:
        """
        Get a registered strategy by name.
        
        Args:
            name: Strategy identifier
        
        Returns:
            Strategy instance or None if not found
        """
        return self._strategies.get(name)
    
    def execute_strategy(self, name: str, operation: Callable[[], Any],
                        **kwargs) -> Any:
        """
        Execute a registered strategy.
        
        Args:
            name: Strategy identifier
            operation: Operation to recover
            **kwargs: Strategy-specific parameters
        
        Returns:
            Result of operation
        
        Raises:
            ValueError: If strategy not found
        """
        strategy = self.get_strategy(name)
        
        if strategy is None:
            raise ValueError(f"Recovery strategy '{name}' not found")
        
        logger.info(f"Executing recovery strategy: {name}")
        return strategy.execute(operation, **kwargs)
    
    def list_strategies(self) -> List[str]:
        """List all registered strategy names"""
        return list(self._strategies.keys())
    
    def get_all_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all registered strategies"""
        return {
            name: strategy.get_description()
            for name, strategy in self._strategies.items()
        }

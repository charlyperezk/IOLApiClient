"""
Circuit breaker implementation for preventing cascading failures.
"""
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any, Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5           # Number of failures before opening
    recovery_timeout: float = 60.0       # Seconds to wait before trying again
    success_threshold: int = 2           # Number of successes to close circuit
    timeout: float = 30.0               # Request timeout


@dataclass
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    config: CircuitBreakerConfig
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitState = CircuitState.CLOSED

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker."""
        async def async_wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.config.success_threshold:
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time()
                
                if (self.state == CircuitState.CLOSED and 
                    self.failure_count >= self.config.failure_threshold):
                    self.state = CircuitState.OPEN
                elif self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.OPEN
                
                raise e
        
        return async_wrapper

    def reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }
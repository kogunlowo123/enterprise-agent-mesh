"""Circuit breaker state machine with thread-safe state transitions."""

from __future__ import annotations

import enum
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)


class CircuitState(str, enum.Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class CircuitBreakerStats:
    """Runtime statistics for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    half_open_calls: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.monotonic)
    total_requests: int = 0
    total_failures: int = 0


class CircuitBreaker:
    """Thread-safe circuit breaker state machine.

    States:
        CLOSED  -> all requests pass through
        OPEN    -> all requests fail fast (no forwarding)
        HALF_OPEN -> limited requests allowed to test recovery

    Transitions:
        CLOSED  --[failures >= threshold]--> OPEN
        OPEN    --[timeout elapsed]---------> HALF_OPEN
        HALF_OPEN --[success]----------------> CLOSED
        HALF_OPEN --[failure]----------------> OPEN
    """

    def __init__(
        self,
        node_id: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[str, CircuitState, CircuitState], None] | None = None,
    ) -> None:
        self.node_id = node_id
        self.config = config or CircuitBreakerConfig()
        self._stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._on_state_change = on_state_change

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._stats.state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._stats.failure_count

    def record_success(self) -> None:
        """Record a successful call. Transitions HALF_OPEN -> CLOSED on threshold."""
        with self._lock:
            self._stats.total_requests += 1
            previous_state = self._stats.state

            if self._stats.state == CircuitState.HALF_OPEN:
                self._stats.success_count += 1
                if self._stats.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._stats.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call. May transition CLOSED -> OPEN or HALF_OPEN -> OPEN."""
        with self._lock:
            self._stats.total_requests += 1
            self._stats.total_failures += 1
            self._stats.failure_count += 1
            self._stats.last_failure_time = time.monotonic()

            if self._stats.state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._stats.state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def allow_request(self) -> bool:
        """Check whether a request should be allowed through.

        - CLOSED: always allow
        - OPEN: allow only if recovery timeout has elapsed (probe attempt)
        - HALF_OPEN: allow limited probe requests
        """
        with self._lock:
            if self._stats.state == CircuitState.CLOSED:
                return True

            if self._stats.state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._stats.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False

            if self._stats.state == CircuitState.HALF_OPEN:
                if self._stats.half_open_calls < self.config.half_open_max_calls:
                    self._stats.half_open_calls += 1
                    return True
                return False

        return False  # unreachable but satisfies type checker

    def force_open(self, reason: str = "") -> None:
        """Manually open the circuit."""
        with self._lock:
            self._stats.last_failure_time = time.monotonic()
            self._transition_to(CircuitState.OPEN)
            logger.warning("Circuit %s force-opened: %s", self.node_id, reason)

    def force_close(self) -> None:
        """Manually close and reset the circuit."""
        with self._lock:
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._stats.half_open_calls = 0
            self._transition_to(CircuitState.CLOSED)

    def get_stats(self) -> dict:
        """Return a snapshot of current circuit breaker stats."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "state": self._stats.state,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "total_requests": self._stats.total_requests,
                "total_failures": self._stats.total_failures,
                "last_failure_time": self._stats.last_failure_time,
                "last_state_change": self._stats.last_state_change,
            }

    def _transition_to(self, new_state: CircuitState) -> None:
        """Internal state transition. Caller must hold the lock."""
        old_state = self._stats.state
        if old_state == new_state:
            return

        self._stats.state = new_state
        self._stats.last_state_change = time.monotonic()

        if new_state == CircuitState.HALF_OPEN:
            self._stats.half_open_calls = 0
            self._stats.success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._stats.half_open_calls = 0

        logger.info(
            "Circuit %s: %s -> %s",
            self.node_id,
            old_state.value,
            new_state.value,
        )

        if self._on_state_change is not None:
            self._on_state_change(self.node_id, old_state, new_state)

        self._emit_cloud_event(old_state, new_state)

    def _emit_cloud_event(self, old_state: CircuitState, new_state: CircuitState) -> None:
        """Emit a CloudEvent for circuit state changes."""
        event = {
            "specversion": "1.0",
            "type": "circuit.opened" if new_state == CircuitState.OPEN else "circuit.changed",
            "source": f"enterprise-agent-mesh/circuit-breaker/{self.node_id}",
            "id": f"{self.node_id}-{int(time.time() * 1000)}",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": {
                "node_id": self.node_id,
                "previous_state": old_state.value,
                "new_state": new_state.value,
                "failure_count": self._stats.failure_count,
            },
        }
        logger.info("CloudEvent: %s", json.dumps(event))


class CircuitBreakerRegistry:
    """Registry managing multiple circuit breakers."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        node_id: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[str, CircuitState, CircuitState], None] | None = None,
    ) -> CircuitBreaker:
        with self._lock:
            if node_id not in self._breakers:
                self._breakers[node_id] = CircuitBreaker(
                    node_id=node_id,
                    config=config,
                    on_state_change=on_state_change,
                )
            return self._breakers[node_id]

    def get(self, node_id: str) -> CircuitBreaker | None:
        return self._breakers.get(node_id)

    def all_stats(self) -> list[dict]:
        return [cb.get_stats() for cb in self._breakers.values()]


# Module-level singleton registry
registry = CircuitBreakerRegistry()

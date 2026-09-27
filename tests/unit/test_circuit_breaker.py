"""Unit tests for circuit breaker state machine."""

from __future__ import annotations

import time

import pytest

from agent_runtime.tools.circuit_control import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitState,
)


@pytest.fixture
def config() -> CircuitBreakerConfig:
    return CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        half_open_max_calls=3,
        success_threshold=2,
    )


@pytest.fixture
def breaker(config: CircuitBreakerConfig) -> CircuitBreaker:
    return CircuitBreaker(node_id="test-node", config=config)


class TestCircuitBreakerClosedToOpen:
    """Test CLOSED -> OPEN transition on failure threshold."""

    def test_initial_state_is_closed(self, breaker: CircuitBreaker) -> None:
        assert breaker.state == CircuitState.CLOSED

    def test_single_failure_stays_closed(self, breaker: CircuitBreaker) -> None:
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1

    def test_four_failures_stay_closed(self, breaker: CircuitBreaker) -> None:
        for _ in range(4):
            breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 4

    def test_five_failures_open_circuit(self, breaker: CircuitBreaker) -> None:
        """CLOSED -> OPEN after exactly 5 failures."""
        for _ in range(5):
            breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_requests_rejected_when_open(self, breaker: CircuitBreaker) -> None:
        for _ in range(5):
            breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.allow_request() is False

    def test_success_resets_failure_count(self, breaker: CircuitBreaker) -> None:
        for _ in range(3):
            breaker.record_failure()
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerOpenToHalfOpen:
    """Test OPEN -> HALF_OPEN transition after recovery timeout."""

    def test_transitions_to_half_open_after_timeout(self) -> None:
        """OPEN -> HALF_OPEN after recovery_timeout elapses."""
        fast_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.01,  # 10ms for fast test
        )
        cb = CircuitBreaker(node_id="timeout-node", config=fast_config)

        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.05)  # Wait past recovery_timeout
        allowed = cb.allow_request()
        assert allowed is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_no_half_open_before_timeout(self) -> None:
        """OPEN circuit rejects requests before timeout elapses."""
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        cb = CircuitBreaker(node_id="no-timeout-node", config=config)
        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # Timeout is 60s, we didn't wait
        assert cb.allow_request() is False
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerHalfOpenToClosed:
    """Test HALF_OPEN -> CLOSED on successful probe."""

    def test_half_open_to_closed_on_success(self) -> None:
        """HALF_OPEN -> CLOSED after success_threshold successes."""
        fast_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.01,
            success_threshold=2,
        )
        cb = CircuitBreaker(node_id="half-open-node", config=fast_config)

        for _ in range(5):
            cb.record_failure()
        time.sleep(0.05)

        cb.allow_request()  # Triggers OPEN -> HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN  # Need 2 successes

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self) -> None:
        """HALF_OPEN -> OPEN on any failure."""
        fast_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.01,
        )
        cb = CircuitBreaker(node_id="half-open-fail-node", config=fast_config)

        for _ in range(5):
            cb.record_failure()
        time.sleep(0.05)

        cb.allow_request()  # OPEN -> HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerForceOperations:
    """Test manual circuit breaker controls."""

    def test_force_open(self, breaker: CircuitBreaker) -> None:
        breaker.force_open("test reason")
        assert breaker.state == CircuitState.OPEN
        assert breaker.allow_request() is False

    def test_force_close(self, breaker: CircuitBreaker) -> None:
        for _ in range(5):
            breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        breaker.force_close()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.allow_request() is True


class TestCircuitBreakerRegistry:
    """Test the circuit breaker registry."""

    def test_get_or_create_new(self) -> None:
        reg = CircuitBreakerRegistry()
        cb = reg.get_or_create("new-node")
        assert cb.node_id == "new-node"
        assert cb.state == CircuitState.CLOSED

    def test_get_or_create_returns_same_instance(self) -> None:
        reg = CircuitBreakerRegistry()
        cb1 = reg.get_or_create("same-node")
        cb2 = reg.get_or_create("same-node")
        assert cb1 is cb2

    def test_get_nonexistent_returns_none(self) -> None:
        reg = CircuitBreakerRegistry()
        assert reg.get("nonexistent") is None

    def test_all_stats(self) -> None:
        reg = CircuitBreakerRegistry()
        reg.get_or_create("node-a")
        reg.get_or_create("node-b")
        stats = reg.all_stats()
        assert len(stats) == 2
        node_ids = {s["node_id"] for s in stats}
        assert node_ids == {"node-a", "node-b"}


class TestCircuitBreakerStateChangeCallback:
    """Test state change callbacks."""

    def test_callback_called_on_open(self) -> None:
        transitions: list[tuple] = []

        def on_change(node_id: str, old: CircuitState, new: CircuitState) -> None:
            transitions.append((node_id, old.value, new.value))

        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        cb = CircuitBreaker(node_id="cb-node", config=config, on_state_change=on_change)

        for _ in range(5):
            cb.record_failure()

        assert len(transitions) == 1
        assert transitions[0] == ("cb-node", "CLOSED", "OPEN")

    def test_callback_called_on_close(self) -> None:
        transitions: list[tuple] = []

        def on_change(node_id: str, old: CircuitState, new: CircuitState) -> None:
            transitions.append((old.value, new.value))

        fast_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.01,
            success_threshold=1,
        )
        cb = CircuitBreaker(node_id="cb-close-node", config=fast_config, on_state_change=on_change)

        for _ in range(5):
            cb.record_failure()
        time.sleep(0.05)
        cb.allow_request()  # OPEN -> HALF_OPEN
        cb.record_success()  # HALF_OPEN -> CLOSED

        assert ("CLOSED", "OPEN") in transitions
        assert ("OPEN", "HALF_OPEN") in transitions
        assert ("HALF_OPEN", "CLOSED") in transitions

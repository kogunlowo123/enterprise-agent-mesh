"""Chaos tests for circuit breaker behavior under failure conditions."""

from __future__ import annotations

import time

import pytest

from agent_runtime.tools.circuit_control import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class TestCircuitOpenOnFailure:
    """Chaos tests: verify circuit opens under sustained failure conditions."""

    def test_circuit_opens_under_burst_failures(self) -> None:
        """Rapid burst of failures should open the circuit."""
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        cb = CircuitBreaker(node_id="burst-node", config=config)

        # Simulate burst of failures
        for i in range(10):
            cb.record_failure()
            if i < 4:
                assert cb.state == CircuitState.CLOSED, f"Should stay CLOSED at failure {i+1}"
            else:
                assert cb.state == CircuitState.OPEN, f"Should be OPEN at failure {i+1}"

    def test_circuit_isolates_after_timeout_and_re_failure(self) -> None:
        """After HALF_OPEN probe fails, circuit should re-open."""
        fast_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.02,
        )
        cb = CircuitBreaker(node_id="chaos-node", config=fast_config)

        # Open the circuit
        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery
        time.sleep(0.05)

        # Probe - goes to HALF_OPEN
        cb.allow_request()
        assert cb.state == CircuitState.HALF_OPEN

        # Probe fails - re-opens
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Still rejects requests
        assert cb.allow_request() is False

    def test_multiple_cycles_of_open_close(self) -> None:
        """Circuit should handle multiple open/close cycles correctly."""
        fast_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=1,
        )
        cb = CircuitBreaker(node_id="multi-cycle-node", config=fast_config)

        for cycle in range(3):
            # Open the circuit
            for _ in range(3):
                cb.record_failure()
            assert cb.state == CircuitState.OPEN, f"Cycle {cycle}: should be OPEN"

            # Wait for recovery
            time.sleep(0.05)
            cb.allow_request()  # OPEN -> HALF_OPEN
            assert cb.state == CircuitState.HALF_OPEN

            # Recover
            cb.record_success()
            assert cb.state == CircuitState.CLOSED, f"Cycle {cycle}: should be CLOSED"

    def test_partial_failures_do_not_open_circuit(self) -> None:
        """Failures below threshold with successes mixed in should not open circuit."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(node_id="partial-fail-node", config=config)

        # 4 failures interspersed with successes
        for _ in range(4):
            cb.record_failure()
            cb.record_success()  # Resets failure count

        assert cb.state == CircuitState.CLOSED

    def test_concurrent_failures_thread_safety(self) -> None:
        """Circuit breaker should handle concurrent failures thread-safely."""
        import threading

        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(node_id="concurrent-node", config=config)

        errors: list[Exception] = []

        def record_failures() -> None:
            try:
                for _ in range(10):
                    cb.record_failure()
                    cb.allow_request()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=record_failures) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        # After 100 total failures, circuit must be OPEN
        assert cb.state == CircuitState.OPEN

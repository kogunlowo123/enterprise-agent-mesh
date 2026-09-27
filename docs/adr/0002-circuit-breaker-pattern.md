# ADR 0002: Circuit Breaker Pattern for Agent Fault Isolation

## Status
Accepted

## Context

AI agent calls can fail due to:
- LLM provider outages
- Network partitions between clouds
- Downstream service overload
- Agent timeout exhaustion

Without isolation, cascading failures can bring down the entire mesh.

## Decision

Implement the **circuit breaker pattern** at the agent mesh routing layer with three states:

- **CLOSED**: Normal operation; all requests forwarded
- **OPEN**: Fail-fast; requests rejected without forwarding (recovery timer running)
- **HALF_OPEN**: Probe state; limited requests forwarded to test recovery

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| failure_threshold | 5 | Consecutive failures to open circuit |
| recovery_timeout | 60s | Time before OPEN -> HALF_OPEN probe |
| success_threshold | 2 | Successes to close from HALF_OPEN |
| half_open_max_calls | 3 | Max concurrent probes in HALF_OPEN |

### Placement

Circuit breakers are managed by the `circuit-breaker` (T1) agent and enforced in the `mesh-router` (T0) agent during endpoint selection.

### CloudEvents

State transitions emit CloudEvents:
- `circuit.opened`: CLOSED -> OPEN
- `circuit.changed`: Any other transition
- `topology.changed`: When circuit state affects mesh topology

## Consequences

### Positive
- Prevents cascading failures across agent mesh nodes
- Fast failure detection and automatic recovery
- Observable state via CloudEvents

### Negative
- False positives possible with transient network issues
- OPEN circuit adds latency to legitimate traffic discovery
- State must be shared across mesh-router replicas (Redis-backed in production)

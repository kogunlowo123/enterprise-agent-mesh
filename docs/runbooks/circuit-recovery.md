# Runbook: Circuit Breaker Recovery

## Overview

This runbook covers procedures for recovering from open circuit breakers in the Enterprise Agent Mesh.

## Symptoms

- `GET /api/v1/mesh/health` returns `mesh_state: DEGRADED` or `CRITICAL`
- Routing requests returning 503 errors
- CloudEvents `circuit.opened` firing repeatedly

## Diagnosis

### 1. Check Mesh Health

```bash
curl -s http://api:8000/api/v1/mesh/health | jq .
```

Expected output: identify nodes with `circuit_state: OPEN`.

### 2. Check Topology

```bash
curl -s http://api:8000/api/v1/mesh/topology | jq '.nodes[] | select(.circuit_state == "OPEN")'
```

### 3. Check Logs

```bash
kubectl logs -n enterprise-agent-mesh -l app=api --tail=100 | grep circuit
```

## Recovery Procedures

### Automatic Recovery

Circuit breakers automatically transition OPEN -> HALF_OPEN after `CIRCUIT_RECOVERY_TIMEOUT` (default: 60s). If the probe succeeds, the circuit closes.

### Manual Reset (Single Node)

```bash
curl -X POST http://api:8000/api/v1/circuit/break \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "agent-runtime-aws", "action": "close", "reason": "manual_recovery"}'
```

### Break Glass (All Circuits)

Use the break glass script for emergency recovery:

```bash
export BREAK_GLASS_TOKEN=$(vault kv get -field=token secret/break-glass)
export OPERATOR="your-name"
bash deploy/scripts/break_glass.sh
```

## Post-Recovery Validation

1. Verify `mesh_state: HEALTHY` in `/api/v1/mesh/health`
2. Confirm routing succeeds for all node types
3. Review CloudEvents for root cause
4. Update incident report

## Prevention

- Set appropriate `failure_threshold` for expected error rates
- Monitor agent latency P99 for early degradation signals
- Implement retry budgets to prevent failure amplification

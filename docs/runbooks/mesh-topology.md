# Runbook: Mesh Topology Management

## Overview

The Enterprise Agent Mesh operates across three cloud providers. This runbook covers topology management procedures.

## Topology Architecture

```
AWS EKS (us-east-1)           Azure AKS (eastus)         GCP GKE (us-central1)
  agent-runtime-aws    <--mTLS-->  agent-runtime-azure  <--mTLS-->  agent-runtime-gcp
         |                                |                               |
         +-------------------- Istio Service Mesh ----------------------+
                                          |
                              Enterprise Agent Mesh API
```

## Viewing Current Topology

```bash
curl -s http://api:8000/api/v1/mesh/topology | python3 -m json.tool
```

## Adding a New Mesh Node

1. Deploy agent-runtime to the new cluster
2. Register the endpoint in the API registry (currently in `services/api/src/api/routes/v1/mesh.py`)
3. Apply Istio PeerAuthentication to enforce mTLS
4. Verify health: `GET /api/v1/mesh/health`

## Removing a Mesh Node

1. Open the circuit: `POST /api/v1/circuit/break {"action": "open"}`
2. Drain traffic (wait for active requests to complete)
3. Remove node from the endpoint registry
4. Undeploy the agent-runtime

## Monitoring

Key metrics:
- `mesh_healthy_nodes` - gauge
- `circuit_state_changes_total` - counter
- `routing_latency_p99` - histogram

Grafana dashboard: `observability/dashboards/grafana/platform-overview.json`

# Enterprise Agent Mesh

A production-ready multi-cloud service mesh platform for routing AI agent traffic, enforcing circuit breakers, providing load balancing, and managing agent-to-agent communication at enterprise scale.

## Architecture

- **Multi-Cloud**: AWS EKS + Azure AKS + GCP GKE with Istio service mesh
- **Circuit Breaker**: CLOSED/OPEN/HALF_OPEN state machine with configurable thresholds
- **Load Balancing**: Health-aware weighted routing across agent endpoints
- **mTLS**: Mutual TLS enforcement for all agent-to-agent communication
- **Observability**: OpenTelemetry with distributed tracing

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | REST API gateway |
| agent-runtime | 8001 | LangGraph agent orchestration |
| rag-core | 8002 | Retrieval-augmented generation |

## Quick Start

```bash
cp .env.example .env
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/mesh/route | Route agent request to optimal endpoint |
| GET | /api/v1/mesh/topology | Get live mesh topology graph |
| POST | /api/v1/circuit/break | Open circuit breaker for mesh node |
| GET | /api/v1/mesh/health | Health status of all mesh nodes |
| GET | /api/v1/health | Service health check |
| GET | /api/v1/readiness | Readiness probe |

## Development

```bash
uv venv && source .venv/bin/activate
make install
make test
make lint
```

## Infrastructure

Terraform modules for AWS, Azure, and GCP. See `infra/` directory.

```bash
make tf-init-aws
make tf-plan-aws
```

## License

Apache 2.0 — see LICENSE file.

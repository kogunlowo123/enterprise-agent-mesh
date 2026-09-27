# Contributing Guide

## Development Setup

```bash
git clone https://github.com/kogunlowo123/enterprise-agent-mesh.git
cd enterprise-agent-mesh
uv venv
source .venv/bin/activate
make install
```

## Code Standards

- Python 3.12+ with full type annotations
- Pydantic v2 for data models
- FastAPI for HTTP endpoints
- pytest for testing

## Pull Request Process

1. Create feature branch from `main`
2. Write tests for new functionality
3. Run `make test` and `make lint`
4. Submit PR with description

## Commit Convention

```
feat: add circuit breaker HALF_OPEN state
fix: correct load balancer weight calculation
docs: update API endpoint documentation
```

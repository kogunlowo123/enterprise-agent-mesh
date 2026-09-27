# ADR 0001: Istio Service Mesh for Agent Communication

## Status
Accepted

## Context

Enterprise Agent Mesh requires secure, observable agent-to-agent communication across multiple cloud providers (AWS EKS, Azure AKS, GCP GKE). We need:

- mTLS for all inter-agent traffic
- Traffic policy enforcement
- Distributed tracing without code changes
- Service discovery across clouds

## Decision

Use **Istio** as the service mesh layer across all three clouds.

### Rationale

1. **mTLS Auto-injection**: Istio automatically enforces mutual TLS via its sidecar proxy (Envoy), requiring no application code changes.
2. **Multi-cloud Compatibility**: Istio runs on any Kubernetes distribution, enabling consistent policy across AWS EKS, Azure AKS, and GCP GKE.
3. **Traffic Management**: VirtualService and DestinationRule resources allow circuit breaking, retries, and weighted routing natively.
4. **Observability**: Automatic trace propagation via the Envoy sidecar integrates with Jaeger/Zipkin.
5. **Authorization Policies**: AuthorizationPolicy resources enforce fine-grained access control between services.

### Alternatives Considered

- **Linkerd**: Simpler but lacks the full traffic management features needed for circuit breaking.
- **Consul Connect**: Good multi-datacenter support but more complex to integrate with Kubernetes CRDs.
- **App-level mTLS**: Eliminates mesh dependency but requires significant application code and certificate management.

## Consequences

### Positive
- Zero-trust network security without application changes
- Rich observability for debugging agent communication
- Native circuit breaker support via DestinationRule

### Negative
- Adds ~50MB memory overhead per pod (Envoy sidecar)
- Istio control plane requires dedicated resources (~2 CPU, 2GB memory)
- Learning curve for operators unfamiliar with Istio

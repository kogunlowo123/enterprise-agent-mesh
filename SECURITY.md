# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please report security vulnerabilities to security@enterprise-agent-mesh.io.

Do NOT open a public GitHub issue for security vulnerabilities.

### Response Timeline
- Acknowledgment within 24 hours
- Initial assessment within 72 hours
- Resolution timeline communicated within 7 days

## Security Controls

- mTLS enforcement for all agent-to-agent communication
- JWT authentication with short-lived tokens
- OPA policy enforcement
- Signed container images (Cosign)
- Secret rotation via External Secrets Operator

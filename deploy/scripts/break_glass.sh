#!/usr/bin/env bash
# Break glass procedure for emergency circuit recovery
set -euo pipefail

NAMESPACE="enterprise-agent-mesh"
API_URL="${API_URL:-http://localhost:8000}"

echo "=== BREAK GLASS PROCEDURE ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Operator: ${OPERATOR:-unknown}"

if [[ -z "${BREAK_GLASS_TOKEN:-}" ]]; then
  echo "ERROR: BREAK_GLASS_TOKEN must be set"
  exit 1
fi

# Reset all open circuit breakers
echo "Resetting all open circuit breakers..."
curl -X POST "${API_URL}/api/v1/circuit/break" \
  -H "Authorization: Bearer ${BREAK_GLASS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "ALL", "action": "reset_all", "reason": "break_glass_procedure"}'

echo ""
echo "Checking mesh health..."
curl -s "${API_URL}/api/v1/mesh/health" | python3 -m json.tool

echo ""
echo "Break glass procedure complete."

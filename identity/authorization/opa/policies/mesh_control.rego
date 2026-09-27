package mesh.authz

import future.keywords.in

default allow := false

# Allow mesh routing if agent has mesh:route scope
allow if {
    input.action == "mesh:route"
    "mesh:route" in input.token.scopes
}

# Allow topology reads if agent has mesh:read_topology scope
allow if {
    input.action == "mesh:read_topology"
    "mesh:read_topology" in input.token.scopes
}

# Allow circuit reads if agent has circuit:read_state scope
allow if {
    input.action == "circuit:read_state"
    "circuit:read_state" in input.token.scopes
}

# Allow circuit control if agent has circuit:control scope
allow if {
    input.action == "circuit:control"
    "circuit:control" in input.token.scopes
}

# T0 agents can perform any action in their declared namespace
allow if {
    input.token.tier == "T0"
    input.namespace == input.token.namespace
}

# Deny expired tokens
deny if {
    input.token.exp < time.now_ns() / 1000000000
}

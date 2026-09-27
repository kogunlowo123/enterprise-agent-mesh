CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(128) NOT NULL,
    tenant_id VARCHAR(128) NOT NULL,
    token_hash VARCHAR(256) NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    tier VARCHAR(4) NOT NULL DEFAULT 'T1',
    metadata JSONB NOT NULL DEFAULT '{}',
    CONSTRAINT sessions_unique_token UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON agent_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_id ON agent_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON agent_sessions(agent_id, tenant_id)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS token_revocations (
    token_hash VARCHAR(256) PRIMARY KEY,
    revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason VARCHAR(512)
);

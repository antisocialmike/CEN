CREATE TABLE IF NOT EXISTS platform_audit_log (
    id SERIAL PRIMARY KEY,
    actor_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    action VARCHAR(40) NOT NULL,
    target_type VARCHAR(20) NOT NULL
        CHECK (target_type IN ('owner', 'company')),
    target_id INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_platform_audit_log_target
    ON platform_audit_log (target_type, target_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_platform_audit_log_actor
    ON platform_audit_log (actor_id, created_at DESC);

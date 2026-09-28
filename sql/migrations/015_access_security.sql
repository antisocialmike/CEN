ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

UPDATE password_reset_tokens SET used_at = NOW() WHERE used_at IS NULL;

DROP INDEX IF EXISTS idx_password_reset_tokens_code;

ALTER TABLE password_reset_tokens RENAME COLUMN code TO code_hash;

ALTER TABLE password_reset_tokens
    ALTER COLUMN code_hash TYPE VARCHAR(64),
    ADD COLUMN IF NOT EXISTS attempts SMALLINT NOT NULL DEFAULT 0,
    DROP COLUMN IF EXISTS token;

CREATE TABLE IF NOT EXISTS auth_rate_limits (
    bucket VARCHAR(30) NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hits INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (bucket, client_key)
);

CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_window
    ON auth_rate_limits (window_start);

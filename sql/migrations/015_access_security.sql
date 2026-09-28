-- Version de la sesion. Cada token lleva la que tenia la cuenta al emitirse y
-- deja de valer en cuanto cambia: sube al cambiar o restablecer la contrasena.
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

-- Los codigos de recuperacion se buscaban solo por sus seis digitos, sin
-- amarrarlos al correo, y se guardaban en claro. Los que siguen vivos se
-- pidieron con ese esquema: se anulan.
UPDATE password_reset_tokens SET used_at = NOW() WHERE used_at IS NULL;

DROP INDEX IF EXISTS idx_password_reset_tokens_code;

ALTER TABLE password_reset_tokens RENAME COLUMN code TO code_hash;

-- code_hash guarda un HMAC del codigo, nunca el codigo. used_at lo marca como
-- gastado, por usarse o porque se pidio otro despues, y attempts cuenta cada
-- intento de canjearlo. token no se uso nunca.
ALTER TABLE password_reset_tokens
    ALTER COLUMN code_hash TYPE VARCHAR(64),
    ADD COLUMN IF NOT EXISTS attempts SMALLINT NOT NULL DEFAULT 0,
    DROP COLUMN IF EXISTS token;

-- Solicitudes por direccion a las rutas publicas de /auth, en ventanas fijas.
-- Se cuentan en la base y no en memoria por lo mismo que el bloqueo del login:
-- para que valgan con varios procesos y sobrevivan a un reinicio.
CREATE TABLE IF NOT EXISTS auth_rate_limits (
    bucket VARCHAR(30) NOT NULL,
    client_key VARCHAR(64) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hits INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (bucket, client_key)
);

CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_window
    ON auth_rate_limits (window_start);

# Stack Tecnologico

## Backend

- Python 3.11
- FastAPI: framework web y definicion de endpoints.
- Uvicorn: servidor ASGI.
- Pydantic: validacion de datos de entrada y salida.
- python-jose: emision y verificacion de tokens JWT.
- passlib con bcrypt: hash y verificacion de contrasenas.
- psycopg2: driver de conexion a PostgreSQL.

## Base de datos

- PostgreSQL 15.

## Calidad y seguridad

- flake8: estilo y formato de codigo (PEP 8).
- pytest y pytest-cov: pruebas unitarias, de integracion y cobertura.
- Bandit: analisis estatico de seguridad (SAST).

## Infraestructura

- Docker y Docker Compose: contenerizacion de la API y la base de datos.
- GitHub Actions: integracion continua (lint, pruebas y analisis de
  seguridad en cada push y pull request).

## Decisiones tecnicas

- Patron Strategy para el calculo de ISR e IMSS, de forma que cada
  impuesto se pueda sustituir o extender de forma independiente.
- Patron Repository para aislar el acceso a base de datos de la logica
  de negocio.
- Autenticacion sin estado basada en JWT, con control de acceso por rol
  (RBAC) para separar operaciones de administrador y empleado.

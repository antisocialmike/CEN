# CEN - Sistema de Nomina

Plataforma backend con interfaz web para automatizar el calculo de nomina
(ISR e IMSS), con autenticacion JWT, control de acceso por rol (RBAC) y
persistencia de cada recibo generado en una base de datos relacional.

## Arquitectura

El backend esta construido con FastAPI y sigue una separacion por capas:

- `server/src/routes`: define los endpoints HTTP y las dependencias de
  autenticacion/autorizacion de cada uno.
- `server/src/controllers`: contiene la logica de negocio del calculo de
  nomina (`PayrollService`), implementada con el patron Strategy para ISR
  e IMSS.
- `server/src/repositories`: encapsula el acceso a PostgreSQL.
- `server/src/models`: esquemas de entrada/salida con Pydantic.
- `server/src/middlewares`: emision y verificacion de tokens JWT, y el
  control de acceso por rol.
- `server/src/config`: configuracion de conexion a base de datos.
- `server/src/main.py`: instancia principal de FastAPI donde se montan
  las rutas.

El cliente (`client/`) es un espacio reservado para la interfaz web y aun
no tiene implementacion.

## Requisitos

- Python 3.11+
- PostgreSQL 15
- Docker y Docker Compose (opcional, para levantar todo el stack)

## Configuracion

Copiar `.env.example` a `.env` y ajustar los valores, en especial
`JWT_SECRET_KEY` en cualquier ambiente que no sea desarrollo local.

## Ejecucion con Docker Compose

```
docker compose up --build
```

Esto levanta PostgreSQL (con el esquema de `sql/init.sql` ya aplicado) y
la API en `http://localhost:8000`.

## Ejecucion local

```
pip install -r requirements.txt
uvicorn server.src.main:app --reload
```

## Endpoints principales

- `POST /auth/login`: recibe `email` y `password`, devuelve un token JWT
  con el rol del empleado.
- `POST /payroll/calculate`: recibe `employee_id` y `gross_salary`,
  calcula ISR e IMSS, persiste el recibo y lo devuelve. Requiere un token
  con rol `admin`.
- `GET /health`: verificacion de disponibilidad del servicio.

## Pruebas

```
pytest server/tests/ --cov=server/src/ --cov-fail-under=80
```

## Integracion continua

El pipeline de GitHub Actions (`.github/workflows/ci-cd.yml`) ejecuta en
cada push y pull request hacia `develop` y `main`:

1. Linting con flake8.
2. Pruebas unitarias e integracion con pytest, con un umbral minimo de
   cobertura del 80%.
3. Analisis estatico de seguridad con Bandit.

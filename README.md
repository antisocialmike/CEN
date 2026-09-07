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

El cliente (`client/`) es una SPA de React con Vite y TypeScript. Consume
la API con axios, guarda la sesion en `localStorage` y protege las rutas
por rol. El sistema visual completo vive en `client/src/styles/theme.css`.

## Requisitos

- Python 3.11+
- PostgreSQL 15
- Node 20+ y pnpm 12 (para el cliente)
- Docker y Docker Compose (opcional, para levantar todo el stack)

## Configuracion

Copiar `.env.example` a `.env` y ajustar los valores, en especial
`JWT_SECRET_KEY` en cualquier ambiente que no sea desarrollo local.

## Ejecucion con Docker Compose

```
docker compose up --build
```

Esto levanta los tres servicios:

- PostgreSQL, con el esquema de `sql/init.sql` ya aplicado.
- La API en `http://localhost:8000`.
- El cliente en `http://localhost:5173`, compilado y servido por nginx.

El puerto 5173 del cliente no es casual: es el origen que la API autoriza
por CORS a traves de `ALLOWED_ORIGINS`, y el mismo del servidor de
desarrollo, para que no haya que cambiar nada al pasar de uno a otro.

Vite incrusta `VITE_API_BASE_URL` en el bundle al COMPILAR, no al
ejecutar. Apuntar a otra API exige reconstruir la imagen:

```
VITE_API_BASE_URL=https://api.ejemplo.mx docker compose up --build web
```

## Ejecucion local

```
pip install -r requirements.txt
uvicorn server.src.main:app --reload
```

## Ejecucion del cliente

El gestor de paquetes es **pnpm**, fijado en `packageManager` dentro de
`client/package.json`. Con corepack activado (`corepack enable`) no hace
falta instalarlo aparte: se usa la version exacta que declara el proyecto.

```
pnpm --dir client install
pnpm --dir client dev
```

El cliente queda en `http://localhost:5173` y espera la API en la URL de
`VITE_API_BASE_URL` (ver `client/.env.example`).

`client/pnpm-workspace.yaml` fija `minimumReleaseAge`: pnpm rechaza toda
version publicada hace menos de tres dias, que es la ventana en la que se
detecta y retira practicamente todo paquete comprometido. Ese archivo se
copia dentro de la imagen, asi que la misma politica rige en el build del
contenedor y no solo en tu maquina.

## Endpoints principales

- `POST /auth/login`: recibe `email` y `password`, devuelve un token JWT
  con el rol del empleado.
- `POST /payroll/calculate`: recibe `employee_id` y `gross_salary`,
  calcula ISR e IMSS, persiste el recibo y lo devuelve. Requiere un token
  con rol `admin`.
- `GET /employees` y `POST /employees`: lista y da de alta empleados.
  Requieren rol `admin`.
- `GET /payroll/receipts`: ultimos 20 recibos emitidos por todo el equipo,
  con el nombre del empleado. Requiere rol `admin`.
- `GET /payroll/my-receipts`: recibos del empleado dueno del token.
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

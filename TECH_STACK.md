# Stack Tecnologico

## Backend

- Python 3.11
- FastAPI: framework web y definicion de endpoints.
- Uvicorn: servidor ASGI.
- Pydantic: validacion de datos de entrada y salida.
- python-jose: emision y verificacion de tokens JWT.
- bcrypt: hash y verificacion de contrasenas.
- psycopg2: driver de PostgreSQL, con pool de conexiones compartido.

## Base de datos

- PostgreSQL 15.

## Calidad y seguridad

- flake8: estilo y formato de codigo (PEP 8).
- pytest y pytest-cov: pruebas unitarias, de integracion y cobertura.
- Bandit: analisis estatico de seguridad (SAST).

## Frontend

- React 19 con TypeScript.
- Vite: servidor de desarrollo y empaquetado.
- React Router: enrutado y proteccion de rutas por rol.
- Motion: transiciones y revelados.
- axios: cliente HTTP con interceptores de token y de sesion expirada.
- Phosphor Icons: iconografia, con `weight="bold"` en toda la aplicacion.
- Satoshi y JetBrains Mono: display e interfaz la primera, cifras la segunda.
- pnpm: gestor de paquetes, fijado por version en `packageManager`.

## Infraestructura

- Docker y Docker Compose: contenerizacion de la base de datos, la API y
  el cliente.
- nginx (imagen sin privilegios): sirve el cliente compilado, con historia
  de rutas para React Router y cache inmutable en los assets con hash.
- GitHub Actions: integracion continua (lint, pruebas y analisis de
  seguridad en cada push y pull request).

## Decisiones tecnicas

- Patron Strategy para el calculo de ISR e IMSS, de forma que cada
  impuesto se pueda sustituir o extender de forma independiente.
- Patron Repository para aislar el acceso a base de datos de la logica
  de negocio, sobre un unico gestor de contexto que abre cursor,
  confirma o revierte la transaccion y devuelve la conexion al pool.
- Migraciones versionadas en `sql/migrations/`, aplicadas por la propia
  API al arrancar y registradas en `schema_migrations`. Sin ORM ni
  herramienta externa: son archivos SQL numerados que corren una sola vez
  dentro de una transaccion. La base queda lista en cualquier entorno y no
  solo en un volumen de Docker recien creado.
- Un recibo por empleado y periodo, garantizado por indice unico y
  resuelto con `INSERT ... ON CONFLICT DO UPDATE`, de forma que corregir
  una nomina reemplaza el recibo en vez de duplicarlo.
- Autenticacion sin estado basada en JWT, con control de acceso por rol
  (RBAC) para separar operaciones de administrador y empleado.
- pnpm en lugar de npm: almacen direccionable por contenido, arbol de
  `node_modules` estricto que impide dependencias fantasma, y una ventana
  minima de publicacion que bloquea versiones recien subidas al registro.
- Sistema visual propio en un solo archivo de tokens, con tres reglas
  cerradas: un unico color de acento, canto vivo salvo en lo interactivo,
  y un solo tema.

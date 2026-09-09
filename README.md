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
- `server/src/config`: lectura de variables de entorno (`settings.py`) y
  pool de conexiones a PostgreSQL (`database.py`).
- `server/src/bootstrap.py`: aplica el esquema y asegura la cuenta
  administradora al arrancar.
- `server/src/main.py`: instancia principal de FastAPI donde se montan
  las rutas y se traducen los errores de base de datos.

El cliente (`client/`) es una SPA de React con Vite y TypeScript. Consume
la API con axios, guarda la sesion en `localStorage` y protege las rutas
por rol. El sistema visual completo vive en `client/src/styles/theme.css`.

## Requisitos

- Python 3.11+
- PostgreSQL 15, o Docker Desktop para levantarlo en un contenedor. La API
  no funciona sin una base de datos accesible: sin ella arranca igualmente
  y responde `503` en cada endpoint que consulta datos.
- Node 20+ y pnpm 12 (para el cliente)

## Configuracion

Copiar `.env.example` a `.env` y ajustar los valores, en especial
`JWT_SECRET_KEY` y `ADMIN_PASSWORD` en cualquier ambiente que no sea
desarrollo local.

La conexion se puede dar de dos formas y `DATABASE_URL` tiene prioridad:

- `DATABASE_URL=postgresql://usuario:clave@host:5432/base`, que es lo que
  entregan los proveedores gestionados como Render.
- Las variables sueltas `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y
  `DB_PASSWORD`.

## Base de datos

Al arrancar, la API aplica las migraciones pendientes de `sql/migrations/`
y crea la cuenta administradora si no existe, usando `ADMIN_EMAIL` y
`ADMIN_PASSWORD`. No hace falta ejecutar nada a mano ni depender de que el
volumen de Postgres sea nuevo.

Cada archivo `.sql` de `sql/migrations/` se aplica una sola vez, en orden
alfabetico, y queda registrado en la tabla `schema_migrations`. Todas las
pendientes corren dentro de una unica transaccion: si una falla, ninguna
queda a medias. Para cambiar el esquema se agrega un archivo nuevo con el
siguiente numero; los ya aplicados no se editan.

Las credenciales por defecto para el primer acceso son `admin@cen.com` y
`admin1234`. En una base nueva esa cuenta arranca marcada para cambio de
contrasena: el primer inicio de sesion obliga a definir una propia antes
de poder usar el sistema. Lo mismo ocurre con cada empleado que da de alta
un administrador, que entra con una contrasena temporal y debe sustituirla.

## Ejecucion con Docker Compose

```
docker compose up --build
```

Esto levanta los tres servicios, cada uno esperando a que el anterior
reporte estado saludable:

- PostgreSQL, con `pg_isready` como sonda de arranque.
- La API en `http://localhost:8000`, que aplica las migraciones al iniciar.
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

Para desarrollar y ejecutar las pruebas hace falta el conjunto completo:

```
pip install -r requirements-dev.txt
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

## Conceptos de nomina

Cada recibo se compone de partidas, guardadas en `payroll_receipt_items`
y separadas en percepciones y deducciones:

| Percepcion | De donde sale |
| --- | --- |
| Sueldo del periodo | El bruto capturado |
| Horas extra | Horas dobles y triples sobre el salario por hora (LFT) |
| Aguinaldo | Dias por el salario diario |
| Prima vacacional | 25% de los dias de vacaciones |
| Bono | Importe libre |

| Deduccion | De donde sale |
| --- | --- |
| ISR | Tarifa mensual sobre la base gravable |
| IMSS | Cuotas obrero sobre el sueldo, topadas a 25 UMA |
| Prestamo e Infonavit | Importes libres |

El ISR no se calcula sobre el total percibido sino sobre la **base
gravable**, que descuenta las partes exentas: aguinaldo hasta 30 UMA,
prima vacacional hasta 15 UMA y la mitad de las horas extra con tope de
5 UMA por semana.

### Lo que este modelo simplifica

El calculo es fiel en su estructura pero no sustituye a un sistema
fiscal certificado. En concreto:

- El aguinaldo y la prima vacacional se gravan sumandose a la base del
  mes, no con el procedimiento opcional del articulo 174 del Reglamento
  de la LISR.
- El IMSS se calcula sobre el sueldo del periodo, sin el factor de
  integracion que convierte el salario diario en Salario Base de
  Cotizacion.
- La exencion de horas extra usa cuatro semanas por mes como
  aproximacion, y no distingue a quien percibe el salario minimo, que
  por ley tiene la exencion completa.

## Comprobante de nomina

Cada recibo se puede descargar en PDF, generado en el servidor con los
datos que estan en la base y no con los que trae el navegador.

Es un **comprobante interno**: lleva impreso que no es un CFDI y que no
tiene validez fiscal ante el SAT. Emitir un CFDI de nomina exige un RFC
activo, e.firma, un Certificado de Sello Digital y un contrato con un PAC,
ademas de datos que este sistema no captura (RFC y CURP del empleado, NSS,
regimen fiscal, tipo de contrato y jornada, y el desglose por claves de
catalogo del SAT). El folio y el periodo de cada recibo son unicos, que es
lo que permitiria amarrarlos a un UUID fiscal si algun dia se agrega esa
capa.

## Endpoints principales

- `POST /auth/login`: recibe `email` y `password`, devuelve un token JWT
  con el rol del empleado y `must_change_password`, que indica si la
  cuenta sigue usando la contrasena temporal que le asignaron.
- `POST /auth/password`: cambia la contrasena del dueno del token. Exige
  la contrasena actual, rechaza reutilizar la misma y responde `204`.
- `POST /payroll/calculate`: recibe `employee_id`, `period` (`AAAA-MM`) y
  `gross_salary`, mas los conceptos opcionales
  (`overtime_double_hours`, `overtime_triple_hours`,
  `christmas_bonus_days`, `vacation_days`, `bonus`, `loan_deduction`,
  `housing_credit_deduction`). Calcula ISR e IMSS, persiste el recibo con
  sus partidas y lo devuelve.
  Requiere un token con rol `admin`. Solo existe un recibo por empleado y
  periodo: recalcular el mismo mes reemplaza el anterior y la respuesta lo
  indica en `created`. Cada recibo guarda quien lo proceso.
- `GET /employees` y `POST /employees`: lista y da de alta empleados.
  Requieren rol `admin`.
- `PUT /employees/{id}`: corrige nombre, correo, rol y salario base.
- `POST /employees/{id}/deactivate` y `.../activate`: baja y alta logica.
  Dar de baja conserva los recibos, impide iniciar sesion y bloquea el
  calculo de nomina de esa persona. Un administrador no puede quitarse a
  si mismo el rol ni desactivar su propia cuenta, para que nadie se quede
  fuera del sistema.
- `GET /payroll/receipts`: ultimos 20 recibos emitidos por todo el equipo,
  con el nombre del empleado. Requiere rol `admin`.
- `GET /payroll/my-receipts`: recibos del empleado dueno del token.
- `GET /payroll/receipts/{id}/pdf`: descarga el comprobante en PDF. Un
  administrador puede bajar cualquiera; un empleado, solo los suyos.
- `GET /health`: verificacion de disponibilidad del servicio.

## Pruebas

Las del servidor no necesitan una base de datos: la capa de acceso a
datos se sustituye por dobles en cada caso.

```
pytest server/tests/ --cov=server/src/ --cov-fail-under=80
```

Las del cliente corren con Vitest sobre jsdom y cubren las piezas con
logica propia: el formateo de importes y periodos, la sesion en
`localStorage` y las redirecciones de `ProtectedRoute`.

```
pnpm --dir client test
pnpm --dir client lint
pnpm --dir client typecheck
```

## Integracion continua

El pipeline de GitHub Actions (`.github/workflows/ci-cd.yml`) ejecuta en
cada push y pull request hacia `develop` y `main` dos trabajos en
paralelo, y solo si ambos pasan continua con el analisis de seguridad y
el despliegue.

Servidor:

1. Linting con flake8, con la configuracion de `.flake8`.
2. Pruebas unitarias e integracion con pytest, con un umbral minimo de
   cobertura del 80%.

Cliente:

1. Linting con ESLint, que falla ante cualquier advertencia.
2. Verificacion de tipos con `tsc`.
3. Pruebas con Vitest.
4. Compilacion de produccion, para que un fallo de build no llegue a la
   imagen de Docker.

Y despues, sobre ambos:

1. Analisis estatico de seguridad con Bandit.
2. Despliegue, solo en `main`.

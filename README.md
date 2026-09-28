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

Tras `LOGIN_MAX_ATTEMPTS` intentos fallidos (5 por omision) la cuenta
queda bloqueada durante `LOGIN_LOCK_MINUTES` minutos (15 por omision) y
el login responde `429`, incluso con la contrasena correcta. Un acceso
correcto reinicia el contador, y un restablecimiento hecho por un
administrador tambien levanta el bloqueo.

Ese bloqueo protege de la fuerza bruta pero abre la puerta a molestar a
alguien fallando a proposito con su correo. Por eso el bloqueo es
temporal y no permanente.

Ademas del bloqueo por cuenta hay un limite por direccion en las rutas
publicas de `/auth`, contado en la tabla `auth_rate_limits` en ventanas de
`AUTH_RATE_WINDOW_SECONDS` (15 minutos por omision): `LOGIN_RATE_LIMIT`
inicios de sesion (60), `PASSWORD_RESET_REQUEST_RATE_LIMIT` solicitudes de
codigo (5) y `PASSWORD_RESET_VERIFY_RATE_LIMIT` canjes (10). Al pasarse
responde `429` con `Retry-After`. La direccion la resuelve uvicorn: detras
de un proxy, como en Render, hay que definir `FORWARDED_ALLOW_IPS` para que
lea `X-Forwarded-For`; si no, todos comparten la del proxy y el limite los
frena a todos juntos. Es una segunda barrera, no la principal: esa cabecera
la puede falsear el cliente si el proxy no la reescribe.

**Sesiones.** El token no basta por si solo: en cada peticion la API
consulta la cuenta y lo rechaza con `401` si ya no esta activa, si su rol
cambio, si su empresa se desactivo o si su version de sesion
(`employees.token_version`) ya no es la que lleva el token. Esa version sube
al cambiar la contrasena y al restablecerla, asi que ambas cosas cierran
todas las sesiones abiertas de esa cuenta. Mientras una cuenta tenga la
contrasena temporal, la API responde `403` a todo salvo a `POST
/auth/password`: la regla la cumple el servidor, no solo el cliente.

**Recuperacion por correo.** El codigo de seis digitos se amarra al correo
que lo pidio, se guarda como HMAC (nunca en claro), vence en
`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` y admite `PASSWORD_RESET_MAX_ATTEMPTS`
intentos (5). Pedir otro anula el anterior, y cada cuenta puede pedir uno
cada `PASSWORD_RESET_COOLDOWN_SECONDS` (60) y hasta
`PASSWORD_RESET_MAX_PER_HOUR` por hora (5). La solicitud responde `204`
exista o no la cuenta, y el correo sale despues de responder, para que ni
la respuesta ni su demora revelen que correos estan registrados.

El cliente comprueba la expiracion del token antes de dejar entrar al
panel, asi que una sesion vencida manda al login en vez de mostrar una
pantalla que fallaria en la primera peticion.

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

Postgres solo lee `DB_USER` y `DB_PASSWORD` la primera vez, cuando crea el
volumen `postgres_data`. Si despues se cambia `DB_PASSWORD` en `.env`, la
base conserva la clave vieja, la API no puede conectarse y el login
responde `503`. Para alinear la base con `.env` sin perder datos:

```
docker compose up -d db
docker compose exec -T db sh -c 'echo "ALTER ROLE :\"usr\" WITH PASSWORD :'"'"'pw'"'"';" | psql -v usr="$POSTGRES_USER" -v pw="$POSTGRES_PASSWORD" -U "$POSTGRES_USER" -d postgres'
docker compose restart api
```

`GET /health` comprueba la conexion a la base, asi que ese caso aparece
como `api` en estado `unhealthy` en `docker compose ps`.

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

## Periodicidad

La nomina se puede pagar mensual, quincenal o semanalmente. El periodo
no es un mes sino un rango: se captura la periodicidad y el dia de
inicio, y el servidor calcula el fin y los dias realmente pagados. Una
quincena empieza el dia 1 o el 16; la segunda de un mes de 31 dias paga
16 dias, y el salario diario se ajusta solo.

**La tarifa de ISR cambia con la periodicidad**, no basta con dividir el
resultado mensual. La tabla se escala por los dias que el SAT asigna a
cada periodicidad (30.4 mensual, 15.2 quincenal, 7 semanal), igual que
el subsidio y la exencion semanal de horas extra. El efecto es que un
mismo sueldo anual paga el mismo impuesto sin importar cada cuando se
cobre. El IMSS no se escala: se cotiza por los dias del periodo.

Una restriccion de exclusion en la base impide que dos recibos del mismo
empleado cubran dias solapados, asi que no se puede pagar dos veces el
mismo dia ni por error ni por descuido.

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
| IMSS | Cuota obrera sobre el Salario Base de Cotizacion por los dias del periodo, topada a 25 UMA |
| Prestamo e Infonavit | Importes libres |

El ISR no se calcula sobre el total percibido sino sobre la **base
gravable**, que descuenta las partes exentas: aguinaldo hasta 30 UMA,
prima vacacional hasta 15 UMA y la mitad de las horas extra con tope de
5 UMA por semana.

El IMSS del trabajador se calcula sobre el **Salario Base de Cotizacion**:
el salario diario por el factor de integracion (aguinaldo y prima
vacacional de ley segun la antiguedad), entre el salario minimo y 25 UMA.
Es el mismo SBC que usa el costo patronal, asi que trabajador y empresa
cotizan sobre la misma base.

La **antiguedad** se cuenta desde la fecha de ingreso de la persona
(`employees.hire_date`, migracion 016), no desde que se creo su cuenta en
CEN. Las cuentas que ya existian toman como fecha de ingreso la de su alta,
que la migracion 011 ya habia recorrido al primer periodo cobrado; conviene
corregirla desde la pantalla de usuarios para quien entro antes.

**Redondeo.** Todo el calculo usa decimales exactos (`Decimal`) y redondea
a centavos con la mitad hacia arriba, igual que el costo patronal. Con
punto flotante, 235.695 quedaba en 235.69; ahora queda en 235.70.

**Lo que cambia cada anio no esta en el codigo.** La UMA, el salario
minimo, el subsidio para el empleo y la tarifa del ISR se leen de la base
con su vigencia (migraciones 012 y 013), segun la fecha en que empieza el
periodo. Hay parametros de 2025 y 2026; un periodo sin parametros vigentes
no se calcula y la API dice cual falta.

A quien en el periodo solo cobra el **salario minimo** no se le retiene
ISR (LISR art. 96), y su cuota del IMSS la paga el patron (LSS art. 36):
aparece en el costo patronal, no en el recibo.

**Tipos de nomina.** Cada persona cobra por sueldos y salarios (clave SAT
02) o como asimilada a salarios por honorarios (09). Al asimilado se le
retiene ISR con la misma tarifa pero sin subsidio ni exenciones, no cotiza
al IMSS y no tiene horas extra, aguinaldo, prima vacacional ni credito
Infonavit, porque no hay relacion laboral. En su costo patronal no hay IMSS,
SAR ni INFONAVIT, y el ISN depende de si el estado grava a los asimilados.
El recibo guarda con que regimen se calculo.

La **jornada** (diurna 8 h, nocturna 7 h, mixta 7.5 h; LFT art. 61) define
cuantas horas tiene el dia al pagar las horas extra.

### Lo que este modelo simplifica

El calculo es fiel en su estructura pero no sustituye a un sistema
fiscal certificado. En concreto:

- Las tarifas por periodicidad se derivan proporcionalmente de la
  mensual, no se transcriben del Anexo 8 de la Resolucion Miscelanea.
- El aguinaldo y la prima vacacional se gravan sumandose a la base del
  periodo, no con el procedimiento opcional del articulo 174 del Reglamento
  de la LISR.
- El SBC solo integra el salario fijo, el aguinaldo y la prima vacacional
  minimos de ley; las percepciones variables (horas extra, bonos) no.
- El salario minimo es el general: no se distingue la Zona Libre de la
  Frontera Norte.
- El limite del subsidio para el empleo se compara contra la base gravable
  del periodo; el decreto habla de "ingresos". Conviene confirmarlo con un
  contador.
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
  la contrasena actual y rechaza reutilizar la misma. El cambio cierra
  todas las sesiones de la cuenta, tambien la que lo pidio, asi que
  responde `200` con el `access_token` con el que sigue.
- `POST /auth/password-reset/request`: recibe `email` y, si la cuenta existe
  y esta activa, le manda un codigo de seis digitos. Siempre responde `204`.
- `POST /auth/password-reset/verify`: recibe `email`, `code` y
  `new_password`. Con el codigo vigente de esa cuenta fija la contrasena,
  levanta el bloqueo del login y responde `204`; con cualquier otra cosa,
  `400` con el mismo mensaje.
- `POST /employees/{id}/reset-password`: genera una contrasena temporal
  para esa persona, la marca para cambio obligatorio y desbloquea su
  cuenta. Devuelve la contrasena una sola vez, para que el administrador
  se la entregue por un canal seguro. Requiere rol `admin`.
- `POST /payroll/calculate`: recibe `employee_id`, `periodicity`
  (`mensual`, `quincenal` o `semanal`), `period_start` y `gross_salary`,
  mas los conceptos opcionales
  (`overtime_double_hours`, `overtime_triple_hours`,
  `christmas_bonus_days`, `vacation_days`, `bonus`, `loan_deduction`,
  `housing_credit_deduction`). El servidor deduce el fin del periodo y
  los dias pagados. Calcula ISR e IMSS, persiste el recibo con sus
  partidas y lo devuelve.
  Requiere un token con rol `admin`. Solo existe un recibo por empleado y
  periodo: recalcular el mismo mes reemplaza el anterior y la respuesta lo
  indica en `created`. Cada recibo guarda quien lo proceso.
- `GET /employees` y `POST /employees`: lista y da de alta empleados.
  Requieren rol `admin`. El alta acepta `hire_date`; sin ella, la persona
  ingresa hoy.
- `PUT /employees/{id}`: corrige nombre, correo, rol, salario base y fecha
  de ingreso. Sin `hire_date` se conserva la que ya tenia.
- `POST /employees/{id}/deactivate` y `.../activate`: baja y alta logica.
  Dar de baja conserva los recibos, impide iniciar sesion y bloquea el
  calculo de nomina de esa persona. Un administrador no puede quitarse a
  si mismo el rol ni desactivar su propia cuenta, para que nadie se quede
  fuera del sistema.
- `GET /payroll/receipts`: historial de recibos de la empresa activa,
  paginado y con el nombre del empleado. Requiere rol `admin`.
- `GET /payroll/my-receipts`: recibos del empleado dueno del token, paginados
  (`page`, `page_size`).
- `GET /superadmin/summary`: tablero de la plataforma, solo con conteos:
  empresas y personas por rol (activas e inactivas), empresas sin dueno
  activo, altas de empresas y duenos por mes y los ultimos movimientos de la
  bitacora. Requiere rol `superadmin`.
- `GET /admin/summary`: resumen de la empresa activa para su admin: quien
  sigue sin recibo en el mes en curso, totales del ultimo mes con recibos,
  ultimas altas y bajas y cuantos hay en cada tipo de nomina.
- `GET /payroll/my-summary`: tablero del empleado dueno del token: ultimo
  recibo, siguiente periodo estimado, acumulado del ano y neto de sus ultimos
  12 periodos.
- `GET /payroll/receipts/{id}/pdf`: descarga el comprobante en PDF. Un
  administrador puede bajar cualquiera; un empleado, solo los suyos.
- `GET /health`: verificacion de disponibilidad del servicio y de la base
  de datos; responde `503` si la base no esta disponible y, mientras tanto,
  reintenta las migraciones y las cuentas iniciales que quedaron pendientes.

## Pruebas

Las unitarias del servidor no necesitan una base de datos: la capa de
acceso a datos se sustituye por dobles en cada caso.

```
pytest server/tests/ --cov=server/src/ --cov-fail-under=80
```

Las de `server/tests/integration/` corren contra un PostgreSQL de verdad:
aplican todas las migraciones en una base nueva, calculan y guardan un
recibo por la API, piden los tableros de cada rol y recorren la
recuperacion de contrasena hasta el login. Solo corren si esta definida
`TEST_DATABASE_URL`, que apunta a un servidor donde se pueda crear una base:
cada corrida crea la suya con nombre aleatorio y la borra al terminar. Sin
la variable se saltan.

```
docker run -d --rm --name cen-pruebas-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:15-alpine
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:55432/postgres pytest server/tests/integration
```

En PowerShell la variable se define antes con
`$env:TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/postgres"`.

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
   cobertura del 80%. El trabajo levanta un PostgreSQL 15 como servicio y
   define `TEST_DATABASE_URL`, asi que las pruebas de integracion corren
   en cada push.

Cliente:

1. Linting con ESLint, que falla ante cualquier advertencia.
2. Verificacion de tipos con `tsc`.
3. Pruebas con Vitest.
4. Compilacion de produccion, para que un fallo de build no llegue a la
   imagen de Docker.

Y despues, sobre ambos:

1. Analisis estatico de seguridad con Bandit.
2. Despliegue, solo en `main`.

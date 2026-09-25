from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg2 import OperationalError
from psycopg2.errors import ExclusionViolation, UniqueViolation

from .bootstrap import bootstrap_database, database_ready
from .config.database import close_pool
from .config.settings import ALLOWED_ORIGINS
from .routes.admin_routes import router as admin_router
from .routes.analytics_routes import router as analytics_router
from .routes.auth_routes import router as auth_router
from .routes.employee_routes import router as employee_router
from .routes.owner_routes import router as owner_router
from .routes.payroll_routes import router as payroll_router
from .routes.superadmin_routes import router as superadmin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_database()
    yield
    close_pool()


app = FastAPI(title="CEN Payroll API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Base de datos no disponible"},
    )


@app.exception_handler(UniqueViolation)
async def duplicated_record(request: Request, exc: UniqueViolation):
    if exc.diag.constraint_name == "companies_rfc_key":
        detail = "El RFC ya esta registrado"
    else:
        detail = "El correo ya esta registrado"
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail},
    )


@app.exception_handler(ExclusionViolation)
async def overlapping_period(request: Request, exc: ExclusionViolation):
    if exc.diag.constraint_name == "company_risk_premiums_no_overlap":
        detail = "Ya hay una prima de riesgo registrada desde esa fecha"
    else:
        detail = "Ese empleado ya tiene un recibo que cubre esos dias"
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail},
    )


app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(payroll_router)
app.include_router(superadmin_router)
app.include_router(owner_router)
app.include_router(analytics_router)
app.include_router(admin_router)


@app.get("/health")
def health_check(response: Response):
    if not database_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": "Base de datos no disponible"}
    return {"status": "ok"}

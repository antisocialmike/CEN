from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg2 import OperationalError
from psycopg2.errors import UniqueViolation

from .bootstrap import bootstrap_database
from .config.database import close_pool
from .config.settings import ALLOWED_ORIGINS
from .routes.auth_routes import router as auth_router
from .routes.employee_routes import router as employee_router
from .routes.payroll_routes import router as payroll_router


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
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "El correo ya esta registrado"},
    )


app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(payroll_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

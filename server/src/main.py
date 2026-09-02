from fastapi import FastAPI
from server.src.routes.payroll_routes import router as payroll_router
from server.src.routes.auth_routes import router as auth_router

app = FastAPI(title="CEN Payroll API")
app.include_router(auth_router)
app.include_router(payroll_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

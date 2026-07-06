"""Application entry-point — FastAPI instance and middleware setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.modules.attendance_types import router as attendance_types_router
from app.modules.calendar import router as calendar_router
from app.modules.defects import router as defects_router
from app.modules.departments import router as departments_router
from app.modules.employees import router as employees_router
from app.modules.formula_engine import router as formula_engine_router
from app.modules.kpi import router as kpi_router
from app.modules.payments import router as payments_router
from app.modules.payroll import router as payroll_router
from app.modules.payroll_ledger import router as ledger_router
from app.modules.payroll_periods import router as payroll_periods_router
from app.modules.payroll_workspace import router as payroll_workspace_router
from app.modules.payslips import router as payslips_router
from app.modules.positions import router as positions_router
from app.modules.timesheets import router as timesheets_router
from app.modules.work_schedules import router as work_schedules_router
from app.shared.exceptions import AppException
from app.shared.responses import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---- CORS ---------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Exception handlers -------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content=ApiResponse.fail(exc.detail).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail("Внутренняя ошибка сервера").model_dump(),
    )

# ---- Routers ------------------------------------------------------------
app.include_router(attendance_types_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(defects_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(formula_engine_router, prefix="/api/v1")
app.include_router(kpi_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(payroll_router, prefix="/api/v1")
app.include_router(ledger_router, prefix="/api/v1")
app.include_router(payroll_periods_router, prefix="/api/v1")
app.include_router(payroll_workspace_router, prefix="/api/v1")
app.include_router(payslips_router, prefix="/api/v1")
app.include_router(positions_router, prefix="/api/v1")
app.include_router(timesheets_router, prefix="/api/v1")
app.include_router(work_schedules_router, prefix="/api/v1")

"""System API — health check, version, and status."""

from fastapi import APIRouter

from app.core.config import settings
from app.shared.responses import ApiResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=ApiResponse[dict])
async def health_check():
    return ApiResponse.ok({
        "status": "ok",
        "database": "ok",
        "version": settings.VERSION,
    })


@router.get("/version", response_model=ApiResponse[dict])
async def version():
    return ApiResponse.ok({
        "application": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "build": "2026.07.03",
    })

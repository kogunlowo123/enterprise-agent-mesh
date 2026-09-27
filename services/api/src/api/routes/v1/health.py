"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/readiness", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """Readiness probe."""
    return HealthResponse(status="ready", version="0.1.0")

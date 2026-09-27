"""Enterprise Agent Mesh API - Main application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.tracing import TracingMiddleware
from api.routes.v1 import circuit, health, mesh, topology

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Enterprise Agent Mesh API starting up")
    yield
    logger.info("Enterprise Agent Mesh API shutting down")


app = FastAPI(
    title="Enterprise Agent Mesh API",
    description="Multi-cloud service mesh for AI agent routing and circuit breaking",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TracingMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(mesh.router, prefix="/api/v1/mesh")
app.include_router(circuit.router, prefix="/api/v1/circuit")
app.include_router(topology.router, prefix="/api/v1/mesh")

"""FastAPI application entrypoint — mounts routers, middleware, and startup hooks."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import agent_feed, agent_init
from app.core.config import get_settings
from app.core.logging import get_logger, init_sentry
from app.db.session import check_db_connection


logger = get_logger(__name__)
settings = get_settings()

init_sentry("fastapi")



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Verify DB connectivity on boot. Temporal workflows start per-agent at init, not here."""
    try:
        await check_db_connection()
        logger.info("Database connectivity verified")
    except Exception as exc:  # noqa: BLE001
        logger.error("Database connectivity check failed", extra={"error": str(exc)})
        raise
    yield


app = FastAPI(
    title="Kestrel AI Backend",
    version="0.1.0",
    description="Autonomous AI creator agent — init + feed endpoints.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 400 Bad Request on request body validation failures per API spec."""
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Deploy health check (not part of the evaluator contract)."""
    return {"status": "ok"}


app.include_router(agent_init.router, prefix="/api/agent")
app.include_router(agent_feed.router, prefix="/api/agent")
"""FastAPI application factory.

This module only wires up the app (middleware, routers). Business logic
lives in app/application and app/domain (docs/01-CLAUDE.md rule 4).
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import (
    audit,
    auth,
    availability,
    catalog,
    health,
    public,
    schedule,
    scheduling_config,
    schools,
    users,
)
from app.api.schemas.common import ErrorDetail, ErrorEnvelope
from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.logging import setup_logging


def _domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """The single place a `DomainError` becomes an HTTP response
    (docs/03-ARCHITECTURE.md #27, docs/04-DESIGN.md #24) — route handlers
    never format their own error responses, they just raise."""
    assert isinstance(exc, DomainError)
    envelope = ErrorEnvelope(
        error=ErrorDetail(type=type(exc).__name__, message=exc.message, details=exc.details)
    )
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="TimeForge API",
        description="Constraint-based school timetabling and dynamic rescheduling API.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(DomainError, _domain_error_handler)

    app.include_router(health.router)
    app.include_router(public.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(schools.router)
    app.include_router(catalog.teachers_router)
    app.include_router(catalog.classes_router)
    app.include_router(catalog.subjects_router)
    app.include_router(catalog.rooms_router)
    app.include_router(catalog.school_days_router)
    app.include_router(catalog.time_periods_router)
    app.include_router(catalog.lesson_requirements_router)
    app.include_router(availability.router)
    app.include_router(scheduling_config.router)
    app.include_router(schedule.router)
    app.include_router(audit.router)

    return app


app = create_app()

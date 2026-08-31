"""FastAPI application factory.

This module only wires up the app (middleware, routers). Business logic
lives in app/application and app/domain (docs/01-CLAUDE.md rule 4).
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import (
    audit,
    auth,
    availability,
    catalog,
    collaboration,
    health,
    notifications,
    public,
    schedule,
    scheduling_config,
    schools,
    users,
)
from app.api.schemas.common import ErrorDetail, ErrorEnvelope
from app.core.config import Settings, get_settings
from app.core.errors import DomainError
from app.core.logging import setup_logging
from app.infrastructure.realtime import broadcaster

logger = logging.getLogger(__name__)


def _warn_about_unconfigured_production_settings(settings: Settings) -> None:
    """A loud, startup-time nag for settings that silently degrade instead
    of failing when left unset — real dev conveniences (registration works
    without a reCAPTCHA provider, verification codes log to the console
    instead of emailing), but exactly the kind of thing that's easy to
    forget before a real deployment and dangerous to leave unnoticed:
    unconfigured reCAPTCHA means registration has NO bot protection at all,
    not a degraded version of it. Never blocks startup — only makes the gap
    impossible to miss in the logs."""
    if not settings.recaptcha_secret_key:
        logger.warning(
            "RECAPTCHA_SECRET_KEY is not set — registration has NO bot protection. "
            "Fine for local dev; set a real key before deploying to production."
        )
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning(
            "SMTP_USERNAME/SMTP_PASSWORD are not set — verification codes are "
            "logged to the console instead of emailed. Fine for local dev; "
            "configure real SMTP credentials before deploying to production."
        )
    if not settings.password_check_breached:
        logger.warning(
            "PASSWORD_CHECK_BREACHED is disabled — registration accepts passwords "
            "already known to be in public breach dumps."
        )
    if settings.firestore_emulator_host or settings.firebase_auth_emulator_host:
        logger.warning(
            "Running against the Firebase Emulator Suite (FIRESTORE_EMULATOR_HOST/"
            "FIREBASE_AUTH_EMULATOR_HOST is set) — nothing written this run will "
            "persist. Unset both before deploying to production."
        )


def _domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """The single place a `DomainError` becomes an HTTP response
    (docs/03-ARCHITECTURE.md #27, docs/04-DESIGN.md #24) — route handlers
    never format their own error responses, they just raise."""
    assert isinstance(exc, DomainError)
    envelope = ErrorEnvelope(
        error=ErrorDetail(type=type(exc).__name__, message=exc.message, details=exc.details)
    )
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Synchronous (threadpool) request handlers need a handle on the serving
    # loop to fan out realtime notifications — see
    # `Broadcaster.publish_threadsafe`.
    broadcaster.bind_loop(asyncio.get_running_loop())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    _warn_about_unconfigured_production_settings(settings)

    app = FastAPI(
        title="TimeForge API",
        description="Constraint-based school timetabling and dynamic rescheduling API.",
        version="0.1.0",
        lifespan=_lifespan,
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
    app.include_router(collaboration.router)
    app.include_router(notifications.router)

    return app


app = create_app()

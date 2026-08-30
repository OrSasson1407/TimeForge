"""Liveness/readiness endpoint. No business logic (see docs/02-PRD.md #26 API routes)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}

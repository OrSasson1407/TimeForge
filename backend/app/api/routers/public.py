"""`/public` — the only endpoints that don't require a Bearer token, for
pages a visitor sees before they have any identity at all (docs/02-PRD.md
#28a: the registration flow needs to let someone pick their school before
they've signed up)."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_school_repository
from app.api.schemas.school import PublicSchoolResponse, school_to_public_response
from app.application.repositories import SchoolRepository

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/schools", response_model=list[PublicSchoolResponse])
def list_public_schools(
    repository: SchoolRepository = Depends(get_school_repository),
) -> list[PublicSchoolResponse]:
    return [school_to_public_response(school) for school in repository.list()]

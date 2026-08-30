"""`/schools` — not built on the generic CRUD factory: School is the root
document, not scoped to a school_id (docs/05-DATABASE.md #3)."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_school_repository, require_admin
from app.api.schemas.school import (
    SchoolResponse,
    SchoolUpsertRequest,
    school_from_upsert,
    school_to_response,
)
from app.application.repositories import SchoolRepository
from app.core.errors import NotFoundError
from app.domain.models import User

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("", response_model=list[SchoolResponse])
def list_schools(
    _user: User = Depends(get_current_user),
    repository: SchoolRepository = Depends(get_school_repository),
) -> list[SchoolResponse]:
    return [school_to_response(school) for school in repository.list()]


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: str,
    _user: User = Depends(get_current_user),
    repository: SchoolRepository = Depends(get_school_repository),
) -> SchoolResponse:
    school = repository.get(school_id)
    if school is None:
        raise NotFoundError(f"School {school_id} not found")
    return school_to_response(school)


@router.put("/{school_id}", response_model=SchoolResponse)
def upsert_school(
    school_id: str,
    body: SchoolUpsertRequest,
    _user: User = Depends(require_admin),
    repository: SchoolRepository = Depends(get_school_repository),
) -> SchoolResponse:
    school = school_from_upsert(school_id, body)
    repository.save(school)
    return school_to_response(school)

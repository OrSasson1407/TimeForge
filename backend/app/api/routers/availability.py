"""`/availability` — not on the generic factory: writes are authorized by
ownership (BR-003), not by an admin-only rule. A teacher may submit their
own availability; only an admin may set a class's, or another teacher's.
"""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_availability_repository, get_current_user
from app.api.schemas.availability import (
    AvailabilityResponse,
    AvailabilityUpsertRequest,
    availability_from_upsert,
    availability_to_response,
)
from app.application.repositories import AvailabilityRepository
from app.core.errors import AuthorizationError, NotFoundError
from app.domain.models import OwnerType, User, UserRole

router = APIRouter(prefix="/availability", tags=["availability"])


def _require_can_write(user: User, owner_type: OwnerType, owner_id: str) -> None:
    if user.role is UserRole.ADMIN:
        return
    if owner_type is OwnerType.TEACHER and owner_id == user.teacher_id:
        return  # BR-003: a teacher may write their own record
    raise AuthorizationError("You may only submit your own availability")


@router.get("", response_model=list[AvailabilityResponse])
def list_availability(
    school_id: str = Query(...),
    owner_type: OwnerType | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> list[AvailabilityResponse]:
    if owner_type is not None and owner_id is not None:
        records = repository.list_for_owner(school_id, owner_type, owner_id)
    else:
        records = repository.list_all(school_id)
    return [availability_to_response(record) for record in records]


@router.get("/{availability_id}", response_model=AvailabilityResponse)
def get_availability(
    availability_id: str,
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> AvailabilityResponse:
    record = next((r for r in repository.list_all(school_id) if r.id == availability_id), None)
    if record is None:
        raise NotFoundError(f"Availability {availability_id} not found")
    return availability_to_response(record)


@router.put("/{availability_id}", response_model=AvailabilityResponse)
def upsert_availability(
    availability_id: str,
    body: AvailabilityUpsertRequest,
    school_id: str = Query(...),
    user: User = Depends(get_current_user),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> AvailabilityResponse:
    _require_can_write(user, body.owner_type, body.owner_id)
    record = availability_from_upsert(school_id, availability_id, body)
    repository.save(school_id, record)
    return availability_to_response(record)

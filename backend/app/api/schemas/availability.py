from pydantic import BaseModel, Field

from app.domain.models import Availability, OwnerType


class AvailabilityResponse(BaseModel):
    id: str
    school_id: str
    owner_type: OwnerType
    owner_id: str
    day_id: str | None = None
    time_period_id: str
    is_available: bool
    preference_weight: float


class AvailabilityUpsertRequest(BaseModel):
    owner_type: OwnerType
    owner_id: str = Field(min_length=1)
    day_id: str | None = None
    time_period_id: str = Field(min_length=1)
    is_available: bool = True
    preference_weight: float = 0.0


def availability_to_response(availability: Availability) -> AvailabilityResponse:
    return AvailabilityResponse(
        id=availability.id,
        school_id=availability.school_id,
        owner_type=availability.owner_type,
        owner_id=availability.owner_id,
        day_id=availability.day_id,
        time_period_id=availability.time_period_id,
        is_available=availability.is_available,
        preference_weight=availability.preference_weight,
    )


def availability_from_upsert(
    school_id: str, availability_id: str, body: AvailabilityUpsertRequest
) -> Availability:
    return Availability(
        id=availability_id,
        school_id=school_id,
        owner_type=body.owner_type,
        owner_id=body.owner_id,
        day_id=body.day_id,
        time_period_id=body.time_period_id,
        is_available=body.is_available,
        preference_weight=body.preference_weight,
    )

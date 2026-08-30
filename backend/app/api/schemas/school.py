from pydantic import BaseModel, Field

from app.domain.models import School


class SchoolResponse(BaseModel):
    id: str
    name: str
    timezone: str


class SchoolUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    timezone: str = Field(min_length=1)


class PublicSchoolResponse(BaseModel):
    """Deliberately thinner than SchoolResponse (no timezone) — this is the
    one school-related shape exposed to an unauthenticated caller, for the
    school picker on the registration page."""

    id: str
    name: str


def school_to_response(school: School) -> SchoolResponse:
    return SchoolResponse(id=school.id, name=school.name, timezone=school.timezone)


def school_to_public_response(school: School) -> PublicSchoolResponse:
    return PublicSchoolResponse(id=school.id, name=school.name)


def school_from_upsert(school_id: str, body: SchoolUpsertRequest) -> School:
    return School(id=school_id, name=body.name, timezone=body.timezone)

"""Request/response schemas for the school-scoped catalog entities that
share the generic CRUD shape (docs/04-DESIGN.md #7; `app.api.crud_router`).
Domain enums (Weekday, TimePeriodKind, RoomStatus) are reused directly as
Pydantic field types rather than duplicated (docs/07-CODE_STANDARDS.md
#11: no pointless 1:1 duplication).
"""

from datetime import time

from pydantic import BaseModel, Field

from app.domain.models import (
    Class,
    LessonRequirement,
    Room,
    RoomStatus,
    SchoolDay,
    Subject,
    Teacher,
    TimePeriod,
    TimePeriodKind,
    Weekday,
)

# --- Teacher ---


class TeacherResponse(BaseModel):
    id: str
    school_id: str
    name: str
    email: str
    subject_ids: list[str]
    max_weekly_load: int
    max_consecutive: int


class TeacherUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    subject_ids: list[str] = Field(default_factory=list)
    max_weekly_load: int = 30
    max_consecutive: int = 4


def teacher_to_response(teacher: Teacher) -> TeacherResponse:
    return TeacherResponse(
        id=teacher.id,
        school_id=teacher.school_id,
        name=teacher.name,
        email=teacher.email,
        subject_ids=sorted(teacher.subject_ids),
        max_weekly_load=teacher.max_weekly_load,
        max_consecutive=teacher.max_consecutive,
    )


def teacher_from_upsert(school_id: str, teacher_id: str, body: TeacherUpsertRequest) -> Teacher:
    return Teacher(
        id=teacher_id,
        school_id=school_id,
        name=body.name,
        email=body.email,
        subject_ids=frozenset(body.subject_ids),
        max_weekly_load=body.max_weekly_load,
        max_consecutive=body.max_consecutive,
    )


# --- Class ---


class ClassResponse(BaseModel):
    id: str
    school_id: str
    name: str
    grade: int
    student_count: int
    home_room_id: str | None = None


class ClassUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    grade: int = Field(ge=0)
    student_count: int = Field(gt=0)
    home_room_id: str | None = None


def class_to_response(class_: Class) -> ClassResponse:
    return ClassResponse(
        id=class_.id,
        school_id=class_.school_id,
        name=class_.name,
        grade=class_.grade,
        student_count=class_.student_count,
        home_room_id=class_.home_room_id,
    )


def class_from_upsert(school_id: str, class_id: str, body: ClassUpsertRequest) -> Class:
    return Class(
        id=class_id,
        school_id=school_id,
        name=body.name,
        grade=body.grade,
        student_count=body.student_count,
        home_room_id=body.home_room_id,
    )


# --- Subject ---


class SubjectResponse(BaseModel):
    id: str
    school_id: str
    name: str
    code: str
    required_capability: str | None = None
    max_daily_occurrences: int
    min_spacing_days: int


class SubjectUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    required_capability: str | None = None
    max_daily_occurrences: int = 1
    min_spacing_days: int = 0


def subject_to_response(subject: Subject) -> SubjectResponse:
    return SubjectResponse(
        id=subject.id,
        school_id=subject.school_id,
        name=subject.name,
        code=subject.code,
        required_capability=subject.required_capability,
        max_daily_occurrences=subject.max_daily_occurrences,
        min_spacing_days=subject.min_spacing_days,
    )


def subject_from_upsert(school_id: str, subject_id: str, body: SubjectUpsertRequest) -> Subject:
    return Subject(
        id=subject_id,
        school_id=school_id,
        name=body.name,
        code=body.code,
        required_capability=body.required_capability,
        max_daily_occurrences=body.max_daily_occurrences,
        min_spacing_days=body.min_spacing_days,
    )


# --- Room ---


class RoomResponse(BaseModel):
    id: str
    school_id: str
    name: str
    capacity: int
    room_type: str
    capabilities: list[str]
    status: RoomStatus


class RoomUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    room_type: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    status: RoomStatus = RoomStatus.ACTIVE


def room_to_response(room: Room) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        school_id=room.school_id,
        name=room.name,
        capacity=room.capacity,
        room_type=room.room_type,
        capabilities=sorted(room.capabilities),
        status=room.status,
    )


def room_from_upsert(school_id: str, room_id: str, body: RoomUpsertRequest) -> Room:
    return Room(
        id=room_id,
        school_id=school_id,
        name=body.name,
        capacity=body.capacity,
        room_type=body.room_type,
        capabilities=frozenset(body.capabilities),
        status=body.status,
    )


# --- SchoolDay ---


class SchoolDayResponse(BaseModel):
    id: str
    school_id: str
    weekday: Weekday
    is_active: bool


class SchoolDayUpsertRequest(BaseModel):
    weekday: Weekday
    is_active: bool = True


def school_day_to_response(day: SchoolDay) -> SchoolDayResponse:
    return SchoolDayResponse(
        id=day.id, school_id=day.school_id, weekday=day.weekday, is_active=day.is_active
    )


def school_day_from_upsert(school_id: str, day_id: str, body: SchoolDayUpsertRequest) -> SchoolDay:
    return SchoolDay(id=day_id, school_id=school_id, weekday=body.weekday, is_active=body.is_active)


# --- TimePeriod ---


class TimePeriodResponse(BaseModel):
    id: str
    school_id: str
    index: int
    start_time: time
    end_time: time
    kind: TimePeriodKind


class TimePeriodUpsertRequest(BaseModel):
    index: int = Field(ge=0)
    start_time: time
    end_time: time
    kind: TimePeriodKind = TimePeriodKind.LESSON


def time_period_to_response(period: TimePeriod) -> TimePeriodResponse:
    return TimePeriodResponse(
        id=period.id,
        school_id=period.school_id,
        index=period.index,
        start_time=period.start_time,
        end_time=period.end_time,
        kind=period.kind,
    )


def time_period_from_upsert(
    school_id: str, period_id: str, body: TimePeriodUpsertRequest
) -> TimePeriod:
    return TimePeriod(
        id=period_id,
        school_id=school_id,
        index=body.index,
        start_time=body.start_time,
        end_time=body.end_time,
        kind=body.kind,
    )


# --- LessonRequirement ---


class LessonRequirementResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    subject_id: str
    weekly_periods: int
    required_capability: str | None = None


class LessonRequirementUpsertRequest(BaseModel):
    class_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    weekly_periods: int = Field(gt=0)
    required_capability: str | None = None


def lesson_requirement_to_response(
    requirement: LessonRequirement,
) -> LessonRequirementResponse:
    return LessonRequirementResponse(
        id=requirement.id,
        school_id=requirement.school_id,
        class_id=requirement.class_id,
        subject_id=requirement.subject_id,
        weekly_periods=requirement.weekly_periods,
        required_capability=requirement.required_capability,
    )


def lesson_requirement_from_upsert(
    school_id: str, requirement_id: str, body: LessonRequirementUpsertRequest
) -> LessonRequirement:
    return LessonRequirement(
        id=requirement_id,
        school_id=school_id,
        class_id=body.class_id,
        subject_id=body.subject_id,
        weekly_periods=body.weekly_periods,
        required_capability=body.required_capability,
    )

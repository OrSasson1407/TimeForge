"""The seven school-scoped catalog/config routers, all built from the same
factory (docs/03-ARCHITECTURE.md #26, `app.api.crud_router`)."""

from app.api.crud_router import build_crud_router
from app.api.dependencies import (
    get_class_repository,
    get_lesson_requirement_repository,
    get_room_repository,
    get_school_day_repository,
    get_subject_repository,
    get_teacher_repository,
    get_time_period_repository,
)
from app.api.schemas.catalog import (
    ClassResponse,
    ClassUpsertRequest,
    LessonRequirementResponse,
    LessonRequirementUpsertRequest,
    RoomResponse,
    RoomUpsertRequest,
    SchoolDayResponse,
    SchoolDayUpsertRequest,
    SubjectResponse,
    SubjectUpsertRequest,
    TeacherResponse,
    TeacherUpsertRequest,
    TimePeriodResponse,
    TimePeriodUpsertRequest,
    class_from_upsert,
    class_to_response,
    lesson_requirement_from_upsert,
    lesson_requirement_to_response,
    room_from_upsert,
    room_to_response,
    school_day_from_upsert,
    school_day_to_response,
    subject_from_upsert,
    subject_to_response,
    teacher_from_upsert,
    teacher_to_response,
    time_period_from_upsert,
    time_period_to_response,
)

teachers_router = build_crud_router(
    prefix="/teachers",
    tag="teachers",
    entity_name="Teacher",
    repository_dependency=get_teacher_repository,
    response_model=TeacherResponse,
    upsert_model=TeacherUpsertRequest,
    to_response=teacher_to_response,
    from_upsert=teacher_from_upsert,
)

classes_router = build_crud_router(
    prefix="/classes",
    tag="classes",
    entity_name="Class",
    repository_dependency=get_class_repository,
    response_model=ClassResponse,
    upsert_model=ClassUpsertRequest,
    to_response=class_to_response,
    from_upsert=class_from_upsert,
)

subjects_router = build_crud_router(
    prefix="/subjects",
    tag="subjects",
    entity_name="Subject",
    repository_dependency=get_subject_repository,
    response_model=SubjectResponse,
    upsert_model=SubjectUpsertRequest,
    to_response=subject_to_response,
    from_upsert=subject_from_upsert,
)

rooms_router = build_crud_router(
    prefix="/rooms",
    tag="rooms",
    entity_name="Room",
    repository_dependency=get_room_repository,
    response_model=RoomResponse,
    upsert_model=RoomUpsertRequest,
    to_response=room_to_response,
    from_upsert=room_from_upsert,
)

school_days_router = build_crud_router(
    prefix="/school-days",
    tag="periods",
    entity_name="SchoolDay",
    repository_dependency=get_school_day_repository,
    response_model=SchoolDayResponse,
    upsert_model=SchoolDayUpsertRequest,
    to_response=school_day_to_response,
    from_upsert=school_day_from_upsert,
)

time_periods_router = build_crud_router(
    prefix="/periods",
    tag="periods",
    entity_name="TimePeriod",
    repository_dependency=get_time_period_repository,
    response_model=TimePeriodResponse,
    upsert_model=TimePeriodUpsertRequest,
    to_response=time_period_to_response,
    from_upsert=time_period_from_upsert,
)

lesson_requirements_router = build_crud_router(
    prefix="/lesson-requirements",
    tag="lesson-requirements",
    entity_name="LessonRequirement",
    repository_dependency=get_lesson_requirement_repository,
    response_model=LessonRequirementResponse,
    upsert_model=LessonRequirementUpsertRequest,
    to_response=lesson_requirement_to_response,
    from_upsert=lesson_requirement_from_upsert,
)

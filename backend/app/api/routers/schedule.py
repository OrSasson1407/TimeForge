"""`/schedules` — the scheduling-workflow endpoints (generate, inspect
versions, validate/apply a manual move, publish, compare). `Schedule.id ==
Schedule.school_id` (one schedule per school, docs/05-DATABASE.md #15), so
every endpoint below takes `school_id` as its scoping query param rather
than a separate path segment. All non-GET endpoints are admin-only:
generating and editing a schedule is an administrative action, distinct
from a teacher submitting their own availability (docs/03-ARCHITECTURE.md
#23-24).
"""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_apply_move_use_case,
    get_compare_versions_use_case,
    get_current_user,
    get_generate_schedule_use_case,
    get_publish_schedule_use_case,
    get_reschedule_use_case,
    get_rescheduling_event_repository,
    get_schedule_repository,
    get_schedule_version_repository,
    get_validate_move_use_case,
    require_admin,
)
from app.api.schemas.rescheduling import (
    ReportDisruptionRequest,
    RescheduleResponse,
    ReschedulingEventResponse,
    disruption_cost_to_response,
    rescheduling_event_to_response,
)
from app.api.schemas.schedule import (
    ApplyMoveRequest,
    AssignmentDiffEntry,
    CompareVersionsResponse,
    GenerateScheduleRequest,
    GenerateScheduleResponse,
    ProposedMove,
    PublishRequest,
    ScheduleAssignmentResponse,
    ScheduleResponse,
    ScheduleVersionResponse,
    ValidateMoveResponse,
    ViolationResponse,
    assignment_to_response,
    infeasibility_to_response,
    schedule_to_response,
    stats_to_response,
    version_to_response,
)
from app.application.repositories import (
    ReschedulingEventRepository,
    ScheduleRepository,
    ScheduleVersionRepository,
)
from app.application.use_cases import (
    ApplyMoveUseCase,
    AssignmentDiff,
    CompareVersionsUseCase,
    GenerateScheduleUseCase,
    PublishScheduleUseCase,
    RescheduleUseCase,
    ValidateMoveUseCase,
)
from app.core.errors import NotFoundError
from app.domain.models import User

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=ScheduleResponse)
def get_schedule(
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: ScheduleRepository = Depends(get_schedule_repository),
) -> ScheduleResponse:
    return schedule_to_response(repository.get_or_create(school_id))


@router.post("/generate", response_model=GenerateScheduleResponse)
def generate_schedule(
    body: GenerateScheduleRequest,
    school_id: str = Query(...),
    user: User = Depends(require_admin),
    use_case: GenerateScheduleUseCase = Depends(get_generate_schedule_use_case),
) -> GenerateScheduleResponse:
    outcome = use_case.execute(
        school_id, request_id=body.request_id, reason=body.reason, actor=user
    )
    return GenerateScheduleResponse(
        status=outcome.status,
        version=version_to_response(outcome.version) if outcome.version is not None else None,
        infeasibility=(
            infeasibility_to_response(outcome.infeasibility)
            if outcome.infeasibility is not None
            else None
        ),
        error=outcome.error,
        stats=stats_to_response(outcome.stats),
    )


@router.get("/versions", response_model=list[ScheduleVersionResponse])
def list_schedule_versions(
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: ScheduleVersionRepository = Depends(get_schedule_version_repository),
) -> list[ScheduleVersionResponse]:
    return [version_to_response(v) for v in repository.list_versions(school_id)]


@router.get("/versions/{version_id}", response_model=ScheduleVersionResponse)
def get_schedule_version(
    version_id: str,
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: ScheduleVersionRepository = Depends(get_schedule_version_repository),
) -> ScheduleVersionResponse:
    version = repository.get(school_id, version_id)
    if version is None:
        raise NotFoundError(f"ScheduleVersion {version_id} not found")
    return version_to_response(version)


@router.get("/versions/{version_id}/assignments", response_model=list[ScheduleAssignmentResponse])
def list_schedule_assignments(
    version_id: str,
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: ScheduleVersionRepository = Depends(get_schedule_version_repository),
) -> list[ScheduleAssignmentResponse]:
    return [assignment_to_response(a) for a in repository.list_assignments(school_id, version_id)]


@router.post("/versions/{version_id}/validate-move", response_model=ValidateMoveResponse)
def validate_move(
    version_id: str,
    body: ProposedMove,
    school_id: str = Query(...),
    _user: User = Depends(require_admin),
    use_case: ValidateMoveUseCase = Depends(get_validate_move_use_case),
) -> ValidateMoveResponse:
    outcome = use_case.execute(
        school_id,
        school_id,
        version_id,
        assignment_id=body.assignment_id,
        teacher_id=body.teacher_id,
        room_id=body.room_id,
        day_id=body.day_id,
        time_period_id=body.time_period_id,
    )
    return ValidateMoveResponse(
        result=outcome.result,
        message=outcome.message,
        violation=(
            ViolationResponse(
                constraint_id=outcome.violation.constraint_id,
                severity=outcome.violation.severity,
                message=outcome.violation.message,
                involved_entities=list(outcome.violation.involved_entities),
            )
            if outcome.violation is not None
            else None
        ),
    )


@router.post("/versions/{version_id}/apply-move", response_model=ScheduleAssignmentResponse)
def apply_move(
    version_id: str,
    body: ApplyMoveRequest,
    school_id: str = Query(...),
    user: User = Depends(require_admin),
    use_case: ApplyMoveUseCase = Depends(get_apply_move_use_case),
) -> ScheduleAssignmentResponse:
    updated = use_case.execute(
        school_id,
        school_id,
        version_id,
        assignment_id=body.assignment_id,
        teacher_id=body.teacher_id,
        room_id=body.room_id,
        day_id=body.day_id,
        time_period_id=body.time_period_id,
        expected_version_tag=body.expected_version_tag,
        actor=user,
    )
    return assignment_to_response(updated)


@router.post("/versions/{version_id}/publish", response_model=ScheduleVersionResponse)
def publish_schedule_version(
    version_id: str,
    body: PublishRequest,
    school_id: str = Query(...),
    user: User = Depends(require_admin),
    use_case: PublishScheduleUseCase = Depends(get_publish_schedule_use_case),
) -> ScheduleVersionResponse:
    published = use_case.execute(
        school_id, version_id, expected_version_tag=body.expected_version_tag, actor=user
    )
    return version_to_response(published)


@router.get("/compare", response_model=CompareVersionsResponse)
def compare_schedule_versions(
    from_version_id: str = Query(...),
    to_version_id: str = Query(...),
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    use_case: CompareVersionsUseCase = Depends(get_compare_versions_use_case),
) -> CompareVersionsResponse:
    result = use_case.execute(school_id, from_version_id, to_version_id)

    def to_entry(diff: AssignmentDiff) -> AssignmentDiffEntry:
        return AssignmentDiffEntry(
            lesson_id=diff.lesson_id,
            before=assignment_to_response(diff.before) if diff.before is not None else None,
            after=assignment_to_response(diff.after) if diff.after is not None else None,
        )

    return CompareVersionsResponse(
        from_version_id=result.from_version_id,
        to_version_id=result.to_version_id,
        added=[to_entry(d) for d in result.added],
        removed=[to_entry(d) for d in result.removed],
        moved=[to_entry(d) for d in result.moved],
        unchanged_count=result.unchanged_count,
    )


@router.post("/reschedule", response_model=RescheduleResponse)
def reschedule(
    body: ReportDisruptionRequest,
    school_id: str = Query(...),
    user: User = Depends(require_admin),
    use_case: RescheduleUseCase = Depends(get_reschedule_use_case),
) -> RescheduleResponse:
    outcome = use_case.execute(
        school_id,
        request_id=body.request_id,
        event_type=body.event_type,
        target_entity_id=body.target_entity_id,
        affected_slots=tuple(slot.to_domain() for slot in body.affected_slots),
        reason=body.reason,
        actor=user,
    )
    return RescheduleResponse(
        status=outcome.status,
        version=version_to_response(outcome.version) if outcome.version is not None else None,
        directly_affected_lesson_ids=list(outcome.directly_affected_lesson_ids),
        disruption_cost=(
            disruption_cost_to_response(outcome.disruption_cost)
            if outcome.disruption_cost is not None
            else None
        ),
        infeasibility=(
            infeasibility_to_response(outcome.infeasibility)
            if outcome.infeasibility is not None
            else None
        ),
        error=outcome.error,
    )


@router.get("/rescheduling-events", response_model=list[ReschedulingEventResponse])
def list_rescheduling_events(
    school_id: str = Query(...),
    _user: User = Depends(require_admin),
    repository: ReschedulingEventRepository = Depends(get_rescheduling_event_repository),
) -> list[ReschedulingEventResponse]:
    return [rescheduling_event_to_response(e) for e in repository.list_for_schedule(school_id)]

"""Schedule, ScheduleVersion, ScheduleAssignment response shapes, plus the
request/response shapes for the scheduling workflow endpoints (generate,
validate-move, apply-move, publish, compare) — docs/03-ARCHITECTURE.md #26.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.application.use_cases.schedule_analytics import ScheduleAnalytics
from app.domain.constraints.violation import Severity
from app.domain.models import (
    Schedule,
    ScheduleAssignment,
    ScheduleScoreSummary,
    ScheduleVersion,
    ScheduleVersionStatus,
)
from app.domain.scheduling.infeasibility import BottleneckReport, InfeasibilityResult
from app.domain.scheduling.result import ScheduleResult, SearchStats, SolverStatus

# --- Schedule / ScheduleVersion / ScheduleAssignment ---


class ScheduleResponse(BaseModel):
    id: str
    school_id: str
    active_version_id: str | None = None


def schedule_to_response(schedule: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id, school_id=schedule.school_id, active_version_id=schedule.active_version_id
    )


class ScheduleScoreResponse(BaseModel):
    hard_violations: int
    soft_penalty: float
    quality: float


def score_summary_to_response(score: ScheduleScoreSummary) -> ScheduleScoreResponse:
    return ScheduleScoreResponse(
        hard_violations=score.hard_violations,
        soft_penalty=score.soft_penalty,
        quality=score.quality,
    )


class ScheduleVersionResponse(BaseModel):
    id: str
    schedule_id: str
    status: ScheduleVersionStatus
    created_by: str
    created_at: datetime
    parent_version_id: str | None = None
    score: ScheduleScoreResponse | None = None
    reason: str | None = None
    assignment_count: int
    version_tag: int


def version_to_response(version: ScheduleVersion) -> ScheduleVersionResponse:
    return ScheduleVersionResponse(
        id=version.id,
        schedule_id=version.schedule_id,
        status=version.status,
        created_by=version.created_by,
        created_at=version.created_at,
        parent_version_id=version.parent_version_id,
        score=score_summary_to_response(version.score) if version.score else None,
        reason=version.reason,
        assignment_count=version.assignment_count,
        version_tag=version.version_tag,
    )


class ScheduleAssignmentResponse(BaseModel):
    id: str
    version_id: str
    lesson_id: str
    teacher_id: str
    class_id: str
    room_id: str
    time_period_id: str
    day_id: str


def assignment_to_response(assignment: ScheduleAssignment) -> ScheduleAssignmentResponse:
    return ScheduleAssignmentResponse(
        id=assignment.id,
        version_id=assignment.version_id,
        lesson_id=assignment.lesson_id,
        teacher_id=assignment.teacher_id,
        class_id=assignment.class_id,
        room_id=assignment.room_id,
        time_period_id=assignment.time_period_id,
        day_id=assignment.day_id,
    )


# --- Generate ---


class GenerateScheduleRequest(BaseModel):
    request_id: str = Field(
        min_length=1, description="Idempotency key (docs/04-DESIGN.md #Idempotency)"
    )
    reason: str | None = None


class BottleneckResponse(BaseModel):
    subject_id: str
    required_capability: str | None
    required: int
    available: int
    shortage: int
    affected_class_ids: list[str]
    affected_teacher_ids: list[str]


def bottleneck_to_response(bottleneck: BottleneckReport) -> BottleneckResponse:
    return BottleneckResponse(
        subject_id=bottleneck.subject_id,
        required_capability=bottleneck.required_capability,
        required=bottleneck.required,
        available=bottleneck.available,
        shortage=bottleneck.shortage,
        affected_class_ids=list(bottleneck.affected_class_ids),
        affected_teacher_ids=list(bottleneck.affected_teacher_ids),
    )


class InfeasibilityResponse(BaseModel):
    bottlenecks: list[BottleneckResponse]
    note: str | None = None


def infeasibility_to_response(result: InfeasibilityResult) -> InfeasibilityResponse:
    return InfeasibilityResponse(
        bottlenecks=[bottleneck_to_response(b) for b in result.bottlenecks], note=result.note
    )


class SearchStatsResponse(BaseModel):
    candidates_tried: int
    backtracks: int
    backjumps: int
    duration_seconds: float


def stats_to_response(stats: SearchStats) -> SearchStatsResponse:
    return SearchStatsResponse(
        candidates_tried=stats.candidates_tried,
        backtracks=stats.backtracks,
        backjumps=stats.backjumps,
        duration_seconds=stats.duration_seconds,
    )


class GenerateScheduleResponse(BaseModel):
    status: SolverStatus
    version: ScheduleVersionResponse | None = None
    infeasibility: InfeasibilityResponse | None = None
    error: str | None = None
    stats: SearchStatsResponse


def solve_result_to_stats_response(result: ScheduleResult) -> SearchStatsResponse:
    return stats_to_response(result.stats)


# --- Manual move (validate / apply) ---


class ProposedMove(BaseModel):
    assignment_id: str = Field(min_length=1)
    teacher_id: str = Field(min_length=1)
    room_id: str = Field(min_length=1)
    day_id: str = Field(min_length=1)
    time_period_id: str = Field(min_length=1)


class ViolationResponse(BaseModel):
    constraint_id: str
    severity: Severity
    message: str
    involved_entities: list[str]


class ValidateMoveResponse(BaseModel):
    result: str  # "VALID" | "WARNING" | "INVALID"
    message: str | None = None
    violation: ViolationResponse | None = None


class ApplyMoveRequest(ProposedMove):
    expected_version_tag: int


class PublishRequest(BaseModel):
    expected_version_tag: int


# --- Analytics ---


class TeacherWorkloadResponse(BaseModel):
    teacher_id: str
    teacher_name: str
    assigned_periods: int
    max_weekly_load: int
    load_ratio: float


class RoomUtilizationResponse(BaseModel):
    room_id: str
    room_name: str
    used_slots: int
    available_slots: int
    utilization_ratio: float


class ClassCoverageResponse(BaseModel):
    class_id: str
    class_name: str
    scheduled_periods: int
    required_periods: int
    is_complete: bool


class ScheduleAnalyticsResponse(BaseModel):
    total_assignments: int
    lesson_slots_per_week: int
    workload_spread: float
    teacher_workloads: list[TeacherWorkloadResponse]
    room_utilizations: list[RoomUtilizationResponse]
    class_coverages: list[ClassCoverageResponse]


def analytics_to_response(analytics: ScheduleAnalytics) -> ScheduleAnalyticsResponse:
    return ScheduleAnalyticsResponse(
        total_assignments=analytics.total_assignments,
        lesson_slots_per_week=analytics.lesson_slots_per_week,
        workload_spread=analytics.workload_spread,
        teacher_workloads=[
            TeacherWorkloadResponse(
                teacher_id=w.teacher_id,
                teacher_name=w.teacher_name,
                assigned_periods=w.assigned_periods,
                max_weekly_load=w.max_weekly_load,
                load_ratio=w.load_ratio,
            )
            for w in analytics.teacher_workloads
        ],
        room_utilizations=[
            RoomUtilizationResponse(
                room_id=u.room_id,
                room_name=u.room_name,
                used_slots=u.used_slots,
                available_slots=u.available_slots,
                utilization_ratio=u.utilization_ratio,
            )
            for u in analytics.room_utilizations
        ],
        class_coverages=[
            ClassCoverageResponse(
                class_id=c.class_id,
                class_name=c.class_name,
                scheduled_periods=c.scheduled_periods,
                required_periods=c.required_periods,
                is_complete=c.is_complete,
            )
            for c in analytics.class_coverages
        ],
    )


# --- Compare ---


class AssignmentDiffEntry(BaseModel):
    lesson_id: str
    before: ScheduleAssignmentResponse | None = None
    after: ScheduleAssignmentResponse | None = None


class CompareVersionsResponse(BaseModel):
    from_version_id: str
    to_version_id: str
    added: list[AssignmentDiffEntry]
    removed: list[AssignmentDiffEntry]
    moved: list[AssignmentDiffEntry]
    unchanged_count: int

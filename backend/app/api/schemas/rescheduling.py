"""Request/response schemas for the rescheduling workflow
(docs/03-ARCHITECTURE.md #26 `POST /schedules/reschedule`; docs/04-DESIGN.md
#17). Reuses `InfeasibilityResponse`/`infeasibility_to_response` and
`ScheduleVersionResponse`/`version_to_response` from `schedule.py` rather
than duplicating them.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.schedule import InfeasibilityResponse, ScheduleVersionResponse
from app.domain.models import ReschedulingEvent, ReschedulingEventType
from app.domain.models.value_objects import TimeSlot
from app.domain.rescheduling import DisruptionCost, ReschedulingStatus


class TimeSlotRequest(BaseModel):
    day_id: str = Field(min_length=1)
    time_period_id: str = Field(min_length=1)

    def to_domain(self) -> TimeSlot:
        return TimeSlot(day_id=self.day_id, time_period_id=self.time_period_id)


class TimeSlotResponse(BaseModel):
    day_id: str
    time_period_id: str


class ReportDisruptionRequest(BaseModel):
    request_id: str = Field(
        min_length=1, description="Idempotency key (docs/04-DESIGN.md #Idempotency)"
    )
    event_type: ReschedulingEventType
    target_entity_id: str = Field(min_length=1)
    affected_slots: list[TimeSlotRequest] = Field(min_length=1)
    reason: str = Field(min_length=1)


class ReschedulingEventResponse(BaseModel):
    id: str
    schedule_id: str
    type: ReschedulingEventType
    target_entity_id: str
    affected_slots: list[TimeSlotResponse]
    reason: str
    reported_at: datetime


def rescheduling_event_to_response(event: ReschedulingEvent) -> ReschedulingEventResponse:
    return ReschedulingEventResponse(
        id=event.id,
        schedule_id=event.schedule_id,
        type=event.type,
        target_entity_id=event.target_entity_id,
        affected_slots=[
            TimeSlotResponse(day_id=slot.day_id, time_period_id=slot.time_period_id)
            for slot in event.affected_slots
        ],
        reason=event.reason,
        reported_at=event.reported_at,
    )


class DisruptionCostResponse(BaseModel):
    moved_assignments: int
    changed_rooms: int
    changed_teachers: int
    soft_constraint_penalty_delta: float
    total: float


def disruption_cost_to_response(cost: DisruptionCost) -> DisruptionCostResponse:
    return DisruptionCostResponse(
        moved_assignments=cost.moved_assignments,
        changed_rooms=cost.changed_rooms,
        changed_teachers=cost.changed_teachers,
        soft_constraint_penalty_delta=cost.soft_constraint_penalty_delta,
        total=cost.total,
    )


class RescheduleResponse(BaseModel):
    status: ReschedulingStatus
    version: ScheduleVersionResponse | None = None
    directly_affected_lesson_ids: list[str] = Field(default_factory=list)
    disruption_cost: DisruptionCostResponse | None = None
    infeasibility: InfeasibilityResponse | None = None
    error: str | None = None

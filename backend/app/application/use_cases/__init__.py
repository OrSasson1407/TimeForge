"""Application-layer use cases for the scheduling workflow
(docs/01-CLAUDE.md rule 4, docs/07-CODE_STANDARDS.md #10): route handlers
call exactly one of these, never embed orchestration logic inline. Simple
CRUD (schools, catalog entities, availability) has no use case of its own —
a straight repository call from the router is not "business logic" in the
sense that rule is aimed at.
"""

from app.application.use_cases.apply_move import ApplyMoveUseCase
from app.application.use_cases.compare_versions import (
    AssignmentDiff,
    CompareVersionsResult,
    CompareVersionsUseCase,
)
from app.application.use_cases.generate_schedule import (
    GenerateScheduleOutcome,
    GenerateScheduleUseCase,
)
from app.application.use_cases.list_violations import ListViolationsUseCase
from app.application.use_cases.publish_schedule import PublishScheduleUseCase
from app.application.use_cases.reschedule import RescheduleOutcome, RescheduleUseCase
from app.application.use_cases.validate_move import MoveValidationResult, ValidateMoveUseCase

__all__ = [
    "ApplyMoveUseCase",
    "AssignmentDiff",
    "CompareVersionsResult",
    "CompareVersionsUseCase",
    "GenerateScheduleOutcome",
    "GenerateScheduleUseCase",
    "ListViolationsUseCase",
    "MoveValidationResult",
    "PublishScheduleUseCase",
    "RescheduleOutcome",
    "RescheduleUseCase",
    "ValidateMoveUseCase",
]

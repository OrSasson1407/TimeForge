"""The constraint engine (docs/04-DESIGN.md #10-14): HC-001..HC-009 and
SC-001..SC-010 as independent, unit-testable strategy classes, plus the
ConstraintEvaluator that aggregates them into a single, reused choke point
for both conflict detection (docs/01-CLAUDE.md rule 8) and scoring.
"""

from app.domain.constraints.availability import (
    ClassAvailabilityConstraint,
    TeacherAvailabilityConstraint,
)
from app.domain.constraints.base import HardConstraint
from app.domain.constraints.break_constraint import BreakConstraint
from app.domain.constraints.conflict import (
    ClassConflictConstraint,
    RoomConflictConstraint,
    TeacherConflictConstraint,
)
from app.domain.constraints.distribution import (
    ConsecutiveLessonConstraint,
    SubjectDistributionConstraint,
)
from app.domain.constraints.evaluator import ConstraintEvaluator
from app.domain.constraints.home_room import HomeRoomPreferenceConstraint
from app.domain.constraints.preferences import (
    TeacherPreferredDayConstraint,
    TeacherPreferredPeriodConstraint,
)
from app.domain.constraints.room_capability import RoomCapabilityConstraint
from app.domain.constraints.room_capacity import RoomCapacityConstraint
from app.domain.constraints.score import PenaltyContribution, Score, compute_quality
from app.domain.constraints.soft_base import SoftConstraint
from app.domain.constraints.stability import (
    DisruptionMinimizationConstraint,
    PreservationConstraint,
)
from app.domain.constraints.teacher_gap import TeacherGapConstraint
from app.domain.constraints.utilization import ResourceUtilizationConstraint
from app.domain.constraints.violation import Severity, Violation
from app.domain.constraints.weekly_requirement import WeeklyRequirementConstraint
from app.domain.constraints.workload_balance import ClassWorkloadBalanceConstraint

__all__ = [
    "BreakConstraint",
    "ClassAvailabilityConstraint",
    "ClassConflictConstraint",
    "ClassWorkloadBalanceConstraint",
    "ConsecutiveLessonConstraint",
    "ConstraintEvaluator",
    "DisruptionMinimizationConstraint",
    "HardConstraint",
    "HomeRoomPreferenceConstraint",
    "PenaltyContribution",
    "PreservationConstraint",
    "ResourceUtilizationConstraint",
    "RoomCapabilityConstraint",
    "RoomCapacityConstraint",
    "RoomConflictConstraint",
    "Score",
    "Severity",
    "SoftConstraint",
    "SubjectDistributionConstraint",
    "TeacherAvailabilityConstraint",
    "TeacherConflictConstraint",
    "TeacherGapConstraint",
    "TeacherPreferredDayConstraint",
    "TeacherPreferredPeriodConstraint",
    "Violation",
    "WeeklyRequirementConstraint",
    "compute_quality",
]

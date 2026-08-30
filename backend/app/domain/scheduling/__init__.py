"""The scheduling engine (docs/04-DESIGN.md #9, #14-19): a pure, framework-
free backtracking CSP solver over the hard constraint engine from
`app.domain.constraints`. No FastAPI or Firebase dependency anywhere in
this package (docs/01-CLAUDE.md rules 1-2, NFR-005).
"""

from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.factory import build_scheduling_problem
from app.domain.scheduling.heuristics import (
    LessonDomain,
    build_lesson_domains,
    compute_degrees,
    least_constraining_value_order,
    select_next_lesson,
)
from app.domain.scheduling.infeasibility import (
    BottleneckReport,
    InfeasibilityAnalyzer,
    InfeasibilityResult,
)
from app.domain.scheduling.optimizer import SimulatedAnnealingOptimizer
from app.domain.scheduling.problem import (
    DEFAULT_SOFT_CONSTRAINT_WEIGHTS,
    SchedulingConfig,
    SchedulingProblem,
    build_time_slots,
)
from app.domain.scheduling.result import ScheduleResult, SearchStats, SolverStatus
from app.domain.scheduling.solver import SearchOutcome, SearchRunStats, Solver, run_search
from app.domain.scheduling.state import EMPTY_SCHEDULE_STATE, ScheduleState

__all__ = [
    "DEFAULT_SOFT_CONSTRAINT_WEIGHTS",
    "EMPTY_SCHEDULE_STATE",
    "BottleneckReport",
    "CandidateAssignment",
    "InfeasibilityAnalyzer",
    "InfeasibilityResult",
    "LessonDomain",
    "ScheduleResult",
    "ScheduleState",
    "SchedulingConfig",
    "SchedulingProblem",
    "SearchOutcome",
    "SearchRunStats",
    "SearchStats",
    "SimulatedAnnealingOptimizer",
    "Solver",
    "SolverStatus",
    "build_lesson_domains",
    "build_scheduling_problem",
    "build_time_slots",
    "compute_degrees",
    "least_constraining_value_order",
    "run_search",
    "select_next_lesson",
]

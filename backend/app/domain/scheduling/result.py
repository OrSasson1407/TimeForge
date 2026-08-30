"""ScheduleResult (docs/04-DESIGN.md #14; docs/03-ARCHITECTURE.md "Solver
Requirements"): the solver's outcome always distinguishes VALID, INFEASIBLE,
FAILED, or TIMEOUT — it never hangs and never raises for an ordinary
"no solution" outcome (docs/03-ARCHITECTURE.md #32 Reliability).

`score` is populated for VALID results (post-optimization, docs/04-DESIGN.md
#15) and, best-effort, for TIMEOUT (scoring whatever partial arrangement
was reached) — never for INFEASIBLE/FAILED, which have no schedule to
score.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.constraints.score import Score
from app.domain.scheduling.candidate import CandidateAssignment
from app.domain.scheduling.infeasibility import InfeasibilityResult


class SolverStatus(StrEnum):
    VALID = "VALID"
    INFEASIBLE = "INFEASIBLE"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True)
class SearchStats:
    candidates_tried: int = 0
    backtracks: int = 0
    duration_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    status: SolverStatus
    assignments: tuple[CandidateAssignment, ...] = field(default_factory=tuple)
    score: Score | None = None
    infeasibility: InfeasibilityResult | None = None
    error: str | None = None
    stats: SearchStats = field(default_factory=SearchStats)

    def __post_init__(self) -> None:
        if self.status is SolverStatus.INFEASIBLE and self.infeasibility is None:
            raise ValueError("ScheduleResult: INFEASIBLE status requires an infeasibility report")
        if self.status is SolverStatus.FAILED and not self.error:
            raise ValueError("ScheduleResult: FAILED status requires an error message")

    @property
    def is_valid(self) -> bool:
        return self.status is SolverStatus.VALID

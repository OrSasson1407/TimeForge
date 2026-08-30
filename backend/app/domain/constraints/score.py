"""Score and PenaltyContribution value objects (docs/04-DESIGN.md #3, #13).

`Score` is the scheduling engine's internal evaluation result — distinct
from `app.domain.models.schedule.ScheduleScoreSummary`, the lighter,
breakdown-free record persisted on a ScheduleVersion (docs/05-DATABASE.md
#4). `compute_quality` is how one becomes the other: a `Score` plus a
configured decay constant `k` yields the summary's `quality` figure.
"""

import math
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PenaltyContribution:
    constraint_id: str
    weight: float
    raw_penalty: float
    weighted_penalty: float
    message: str

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ValueError("PenaltyContribution.constraint_id must not be empty")
        if self.raw_penalty < 0:
            raise ValueError("PenaltyContribution.raw_penalty must be >= 0")


@dataclass(frozen=True, slots=True)
class Score:
    hard_violations: int
    soft_penalty: float
    breakdown: tuple[PenaltyContribution, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.hard_violations < 0:
            raise ValueError("Score.hard_violations must be >= 0")
        if self.soft_penalty < 0:
            raise ValueError("Score.soft_penalty must be >= 0")


def compute_quality(soft_penalty: float, k: float, *, lesson_count: int) -> float:
    """docs/04-DESIGN.md #13: `quality := 100 * exp(-k * avgPenaltyPerLesson)`,
    bounded (0, 100] and monotonically decreasing in penalty.

    Decision: decays on `soft_penalty / lesson_count`, not the raw total.
    `soft_penalty` is a sum across every lesson/teacher/class in the
    schedule, so it scales with school size — measured directly against
    the benchmark scenarios (docs/03-ARCHITECTURE.md #30), a single `k`
    against the RAW total made quality collapse to ~0 for any realistically
    imperfect multi-hundred-lesson schedule (Small: penalty 212 -> quality
    0.002; Large: penalty 1998 -> quality effectively 0), which defeats the
    purpose of an explainable 0-100 figure. Dividing by lesson count makes
    quality reflect *average* badness per lesson, which is stable across
    school sizes for a comparably-optimized schedule (Small/Medium/Large
    all land around quality~90 for the same generator+optimizer, matching
    intuition that they're each about as good relative to their own size).
    """
    if soft_penalty < 0:
        raise ValueError("compute_quality: soft_penalty must be >= 0")
    if k <= 0:
        raise ValueError("compute_quality: k must be > 0")
    if lesson_count <= 0:
        raise ValueError("compute_quality: lesson_count must be > 0")
    return 100.0 * math.exp(-k * soft_penalty / lesson_count)

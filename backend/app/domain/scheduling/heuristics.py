"""MRV, degree, and LCV heuristics (docs/04-DESIGN.md #15-16).

Decision: MRV is applied DYNAMICALLY — at every step the search picks
whichever remaining lesson currently has the smallest domain (ties broken
by degree), not a fixed order chosen once before search begins. The
pseudocode in docs/04-DESIGN.md #15 computes the ordering once
(`ordering := orderLessonsByMRVThenDegree(problem)`); measured against the
"Medium" benchmark scenario (docs/03-ARCHITECTURE.md #30), that static
reading caused heavy thrashing — a lesson chosen early from *initial*
domain sizes can easily not be the most-constrained one anymore once
several other lessons have been placed and forward checking has pruned
everything. Re-selecting at each step directs the search toward whatever
is *currently* tightest, which is the standard, more effective form of MRV
and is what actually makes the "performant enough" requirement (master
prompt Phase 4) achievable at realistic scale. docs/04-DESIGN.md #15 has
been updated to describe this.
"""

from collections import Counter
from collections.abc import Sequence

from app.domain.models.lesson import Lesson
from app.domain.models.value_objects import TimeSlot
from app.domain.scheduling.problem import SchedulingProblem
from app.domain.scheduling.state import ScheduleState

LessonDomain = tuple[Lesson, tuple[TimeSlot, ...]]


def compute_degrees(lessons: Sequence[Lesson], problem: SchedulingProblem) -> dict[str, int]:
    """Proxy for 'how constrained is this lesson's neighborhood': lessons
    belonging to the same Class are its most direct competitors for the
    class's limited weekly slots. Static (class membership never changes
    during search), so computed once and reused for every MRV tie-break."""
    class_id_by_lesson = {
        lesson.id: problem.requirement_by_id[lesson.requirement_id].class_id for lesson in lessons
    }
    counts = Counter(class_id_by_lesson.values())
    return {lesson_id: counts[class_id] - 1 for lesson_id, class_id in class_id_by_lesson.items()}


def build_lesson_domains(
    lessons: Sequence[Lesson], problem: SchedulingProblem
) -> tuple[LessonDomain, ...]:
    return tuple((lesson, problem.candidate_slots_for(lesson)) for lesson in lessons)


def select_next_lesson(remaining: Sequence[LessonDomain], degrees: dict[str, int]) -> int:
    """Index (within `remaining`) of the next lesson to try: fewest
    remaining candidate slots first (MRV), ties broken by degree."""
    return min(
        range(len(remaining)),
        key=lambda i: (len(remaining[i][1]), -degrees[remaining[i][0].id]),
    )


def least_constraining_value_order(
    domain: Sequence[TimeSlot], rest: Sequence[LessonDomain]
) -> tuple[TimeSlot, ...]:
    """Try first the slot that leaves the most options open for other
    unplaced lessons: the slot fewest OTHER remaining lessons also want,
    precomputed once as a Counter (O(remaining x avgDomain)) rather than
    re-scanned per candidate."""
    if len(domain) <= 1:
        return tuple(domain)

    slot_counts: Counter[TimeSlot] = Counter()
    for _, other_domain in rest:
        slot_counts.update(other_domain)

    return tuple(sorted(domain, key=lambda slot: slot_counts[slot]))


def forward_check(
    state: ScheduleState, remaining: Sequence[LessonDomain], problem: SchedulingProblem
) -> tuple[LessonDomain, ...] | None:
    """Prune every remaining lesson's slot domain against the new `state`:
    a slot survives only if `resolve_placement` can still find a free
    (teacher, room) pair for it. If any lesson's domain becomes empty, this
    branch is dead (docs/04-DESIGN.md #16)."""
    pruned: list[LessonDomain] = []
    for lesson, domain in remaining:
        new_domain = tuple(
            slot for slot in domain if problem.resolve_placement(lesson, slot, state) is not None
        )
        if not new_domain:
            return None
        pruned.append((lesson, new_domain))
    return tuple(pruned)

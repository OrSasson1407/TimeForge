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
from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class ForwardCheckResult:
    """Either a fully pruned set of domains (`pruned`), or a wipe-out —
    `wiped_out` names the lesson that ran out of slots and `wiped_domain`
    is what it still had *before* this state was applied. Conflict-directed
    backjumping needs that pair to work out whose reconsideration could
    give the lesson its domain back (see `conflicts.domain_wipeout_culprits`);
    plain forward checking only needs to know that the branch is dead."""

    pruned: tuple[LessonDomain, ...] | None
    wiped_out: Lesson | None = None
    wiped_domain: tuple[TimeSlot, ...] = ()


def forward_check_detailed(
    state: ScheduleState,
    remaining: Sequence[LessonDomain],
    problem: SchedulingProblem,
    changed_slot: TimeSlot | None = None,
) -> ForwardCheckResult:
    """Prune every remaining lesson's slot domain against the new `state`:
    a slot survives only if `resolve_placement` can still find a free
    (teacher, room) pair for it. If any lesson's domain becomes empty, this
    branch is dead (docs/04-DESIGN.md #16).

    `changed_slot` makes this INCREMENTAL, which is what makes the search
    tractable at scale. `SchedulingProblem.resolve_placement` reads `state`
    only through `class_assignment_at` / `teacher_assignment_at` /
    `room_assignment_at`, and every one of those is queried *at the slot
    being tested* — so adding an assignment at slot S cannot change the
    answer for any slot other than S. Re-testing only S is therefore exactly
    equivalent to a full re-scan, not an approximation of one.

    The difference is not marginal: on the "Large" benchmark scenario
    (1150 lessons x ~40 slots) a full re-scan costs ~46,000
    `resolve_placement` calls per search node, versus at most one per
    remaining lesson here. Pass `changed_slot=None` for the initial check,
    where no single slot changed and everything genuinely must be examined.
    """
    pruned: list[LessonDomain] = []
    for lesson, domain in remaining:
        if changed_slot is None:
            new_domain = tuple(
                slot
                for slot in domain
                if problem.resolve_placement(lesson, slot, state) is not None
            )
        elif changed_slot in domain:
            if problem.resolve_placement(lesson, changed_slot, state) is None:
                new_domain = tuple(slot for slot in domain if slot != changed_slot)
            else:
                new_domain = tuple(domain)
        else:
            new_domain = tuple(domain)

        if not new_domain:
            return ForwardCheckResult(pruned=None, wiped_out=lesson, wiped_domain=tuple(domain))
        pruned.append((lesson, new_domain))
    return ForwardCheckResult(pruned=tuple(pruned))


def forward_check(
    state: ScheduleState, remaining: Sequence[LessonDomain], problem: SchedulingProblem
) -> tuple[LessonDomain, ...] | None:
    """The plain "did this branch survive?" form of `forward_check_detailed`,
    for callers that don't need to attribute a wipe-out."""
    return forward_check_detailed(state, remaining, problem).pruned

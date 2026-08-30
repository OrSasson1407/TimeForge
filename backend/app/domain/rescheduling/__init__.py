"""The rescheduling engine (docs/04-DESIGN.md #17): "freeze unaffected,
repair the rest" — reuses `app.domain.scheduling`'s own search and
optimizer rather than a second implementation. Pure, framework-free
(docs/01-CLAUDE.md rules 1-2), like every other domain sub-package.
"""

from app.domain.rescheduling.affected import (
    UnsupportedReschedulingEventTypeError,
    identify_affected_assignments,
)
from app.domain.rescheduling.disruption_cost import DisruptionCost, compute_disruption_cost
from app.domain.rescheduling.engine import (
    ReschedulingEngine,
    ReschedulingOutcome,
    ReschedulingStatus,
)
from app.domain.rescheduling.problem_adjustment import (
    augment_availability_for_event,
    augment_rooms_for_event,
)

__all__ = [
    "DisruptionCost",
    "ReschedulingEngine",
    "ReschedulingOutcome",
    "ReschedulingStatus",
    "UnsupportedReschedulingEventTypeError",
    "augment_availability_for_event",
    "augment_rooms_for_event",
    "compute_disruption_cost",
    "identify_affected_assignments",
]

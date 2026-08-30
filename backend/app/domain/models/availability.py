"""Availability entity (docs/04-DESIGN.md #1-2).

One record per (owner, TimePeriod) pair, optionally scoped to a specific
day. `is_available=False` enforces HC-005/HC-006; `preference_weight`
feeds the soft-constraint scoring model for SC-001 (preferred periods) and
SC-002 (preferred days) — higher = more preferred — and is otherwise
ignored.

Decision: `day_id` is optional. When `None`, a record applies to that
TimePeriod on every active day (e.g. "period 3 is generally disliked");
when set, it applies to that specific (day, period) only, and takes
priority over any day-independent record for the same owner+period (e.g.
"...but Tuesday period 3 specifically is fine"). Without day-level
granularity, SC-002 (a teacher's *day* preference, not just their period
preference) has no data to read from — a genuine gap found while
implementing Phase 5's soft constraints, not a hypothetical one.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.models.enums import OwnerType


@dataclass(frozen=True, slots=True)
class Availability:
    id: str
    school_id: str
    owner_type: OwnerType
    owner_id: str
    time_period_id: str
    is_available: bool
    day_id: str | None = None
    preference_weight: float = 0.0

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Availability.id must not be empty")
        if not self.school_id:
            raise ValueError("Availability.school_id must not be empty")
        if not self.owner_id:
            raise ValueError("Availability.owner_id must not be empty")
        if not self.time_period_id:
            raise ValueError("Availability.time_period_id must not be empty")
        if self.day_id is not None and not self.day_id:
            raise ValueError("Availability.day_id must not be an empty string (use None instead)")
        if not math.isfinite(self.preference_weight):
            raise ValueError("Availability.preference_weight must be a finite number")


@dataclass(frozen=True, slots=True)
class AvailabilityIndex:
    """(owner, [day], period) -> Availability, for one owner type. A
    day-specific record (if present) takes priority over a day-independent
    one for the same owner+period; if neither exists, an owner is treated
    as available with neutral (0.0) preference (docs/02-PRD.md #17)."""

    _exact: dict[tuple[str, str, str], Availability] = field(default_factory=dict)
    _day_independent: dict[tuple[str, str], Availability] = field(default_factory=dict)

    def record_for(self, owner_id: str, day_id: str, time_period_id: str) -> Availability | None:
        return self._exact.get((owner_id, day_id, time_period_id)) or self._day_independent.get(
            (owner_id, time_period_id)
        )

    def is_available(self, owner_id: str, day_id: str, time_period_id: str) -> bool:
        record = self.record_for(owner_id, day_id, time_period_id)
        return record.is_available if record is not None else True

    def preference_weight(self, owner_id: str, day_id: str, time_period_id: str) -> float:
        record = self.record_for(owner_id, day_id, time_period_id)
        return record.preference_weight if record is not None else 0.0


def build_availability_index(
    records: Sequence[Availability], owner_type: OwnerType
) -> AvailabilityIndex:
    """Shared by HC-005/HC-006, SC-001/SC-002 (docs/04-DESIGN.md #11-12),
    and the scheduling problem's static candidate pre-filtering — a single
    source of truth for availability/preference lookup and defaults."""
    exact: dict[tuple[str, str, str], Availability] = {}
    day_independent: dict[tuple[str, str], Availability] = {}
    for record in records:
        if record.owner_type is not owner_type:
            continue
        if record.day_id is not None:
            exact[(record.owner_id, record.day_id, record.time_period_id)] = record
        else:
            day_independent[(record.owner_id, record.time_period_id)] = record
    return AvailabilityIndex(_exact=exact, _day_independent=day_independent)

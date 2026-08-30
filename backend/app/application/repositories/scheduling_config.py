"""SchedulingConfigRepository (docs/05-DATABASE.md #19): a singleton
document per school (`schools/{schoolId}/schedulingConfig/current`), not a
collection — `get()` returns the engine's own `SchedulingConfig` (weights,
solver/annealing parameters) directly rather than a parallel persisted
shape, since the persisted document maps onto it field-for-field.
"""

from typing import Protocol

from app.domain.scheduling import SchedulingConfig


class SchedulingConfigRepository(Protocol):
    def get(self, school_id: str) -> SchedulingConfig:
        """Never returns None: a school with no saved config yet gets
        `SchedulingConfig()`'s defaults (docs/05-DATABASE.md #19's
        example values)."""
        ...

    def save(self, school_id: str, config: SchedulingConfig) -> None: ...

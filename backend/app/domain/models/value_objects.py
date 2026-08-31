"""Domain value objects (docs/04-DESIGN.md #3)."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """The atomic scheduling coordinate: one day, one time period.

    Compared and hashed by value so it can key lookup dicts (e.g. a
    teacher's booked slots) without any identity/equality surprises.

    The hash is computed once and stored. This is the hottest single
    operation in the whole engine: TimeSlot keys every slot index and every
    conflict-detection group, and a profile of the "Medium" scenario counted
    **10.8 million** hash calls costing 5.7s of a 23s solve. The generated
    dataclass `__hash__` rebuilds a `(day_id, time_period_id)` tuple on
    every one of those; caching turns each into a slot read. `_hash` is
    excluded from comparison so equality still rests on the two real fields
    alone.
    """

    day_id: str
    time_period_id: str
    _hash: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.day_id:
            raise ValueError("TimeSlot.day_id must not be empty")
        if not self.time_period_id:
            raise ValueError("TimeSlot.time_period_id must not be empty")
        object.__setattr__(self, "_hash", hash((self.day_id, self.time_period_id)))

    def __hash__(self) -> int:
        return self._hash

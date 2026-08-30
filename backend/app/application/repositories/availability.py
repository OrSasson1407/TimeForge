"""AvailabilityRepository (docs/05-DATABASE.md #18): not the generic
`Repository[T]` shape — availability is always read scoped to one owner
(a specific teacher or class), matching the `ownerType, ownerId` composite
index, or read in bulk for building a `SchedulingProblem`.
"""

from typing import Protocol

from app.domain.models import Availability, OwnerType


class AvailabilityRepository(Protocol):
    def list_for_owner(
        self, school_id: str, owner_type: OwnerType, owner_id: str
    ) -> list[Availability]: ...

    def list_all(self, school_id: str) -> list[Availability]:
        """Every availability record for the school — what
        `SchedulingProblem` construction needs (docs/04-DESIGN.md #9)."""
        ...

    def save(self, school_id: str, availability: Availability) -> None: ...

"""ScheduleRepository and ScheduleVersionRepository (docs/04-DESIGN.md #7,
#21; docs/05-DATABASE.md #15-17): the versioning-specific interfaces.

Decision: `Schedule.id == Schedule.school_id`. Every school has exactly one
Schedule (docs/05-DATABASE.md #15), so using the school's own id avoids an
extra query just to find "the" schedule document for a school.
"""

from collections.abc import Sequence
from typing import Protocol

from app.domain.models import Schedule, ScheduleAssignment, ScheduleScoreSummary, ScheduleVersion
from app.domain.scheduling.candidate import CandidateAssignment


class ScheduleRepository(Protocol):
    def get(self, school_id: str) -> Schedule | None: ...

    def get_or_create(self, school_id: str) -> Schedule:
        """A school always has a Schedule once anyone asks for one, even
        before a single version has ever been generated (`activeVersionId`
        stays None until the first publish)."""
        ...


class ScheduleVersionRepository(Protocol):
    def get(self, schedule_id: str, version_id: str) -> ScheduleVersion | None: ...

    def list_versions(self, schedule_id: str) -> list[ScheduleVersion]: ...

    def list_assignments(self, schedule_id: str, version_id: str) -> list[ScheduleAssignment]: ...

    def create_draft(
        self,
        schedule_id: str,
        assignments: Sequence[CandidateAssignment],
        *,
        created_by: str,
        parent_version_id: str | None = None,
        reason: str | None = None,
        score: ScheduleScoreSummary | None = None,
        request_id: str | None = None,
    ) -> ScheduleVersion:
        """Takes the scheduling engine's own `CandidateAssignment`
        (no persisted id yet) rather than `ScheduleAssignment` — minting
        assignment ids is an infrastructure/storage concern, not something
        the caller (an application-layer use case) should have to do
        itself (docs/04-DESIGN.md #32, Factory pattern)."""
        ...

    def apply_assignment_change(
        self,
        schedule_id: str,
        version_id: str,
        updated_assignment: ScheduleAssignment,
        *,
        expected_version_tag: int,
    ) -> None:
        """Raises ConcurrencyError if `expected_version_tag` no longer
        matches the version's current tag (docs/05-DATABASE.md #13) —
        never a silent overwrite (NFR-004). Raises ConflictError if the
        version is not DRAFT (BR-004: published/archived are immutable)."""
        ...

    def update_score(self, schedule_id: str, version_id: str, score: ScheduleScoreSummary) -> None:
        """Persists a freshly recomputed score on a DRAFT version — called
        by `ApplyMoveUseCase` right after `apply_assignment_change` so the
        persisted score never goes stale after a manual move. Without this,
        `publish()`'s BR-005 check would trust a score computed before the
        move, which could let a since-broken schedule publish (or block a
        since-fixed one)."""
        ...

    def publish(self, schedule_id: str, version_id: str, *, expected_version_tag: int) -> None:
        """One atomic operation (docs/04-DESIGN.md #21): the version
        becomes PUBLISHED, the Schedule's `activeVersionId` is updated, and
        the previously-active version (if any) becomes ARCHIVED. Raises
        ValidationError if the version has any hard-constraint violations
        (BR-005) or is not DRAFT; ConcurrencyError on a stale
        `expected_version_tag`."""
        ...

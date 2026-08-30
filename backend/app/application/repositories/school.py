"""SchoolRepository (docs/05-DATABASE.md #3): the one entity NOT nested
under `schools/{schoolId}` — it IS that root document, keyed by its own id."""

from typing import Protocol

from app.domain.models import School


class SchoolRepository(Protocol):
    def get(self, school_id: str) -> School | None: ...

    def list(self) -> list[School]: ...

    def save(self, school: School) -> None: ...

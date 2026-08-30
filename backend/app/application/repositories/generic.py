"""Generic school-scoped CRUD repository interface (docs/04-DESIGN.md #7-8).

Defined in the application layer, not domain: the domain layer never
consumes repositories at all (it's pure computation — entities, constraints,
the scheduling engine); only application-layer use cases load domain
objects via repositories and persist results back through them
(docs/01-CLAUDE.md rules 2-3, docs/03-ARCHITECTURE.md #10-11).

Implementations live in `app.infrastructure.repositories` and are the ONLY
code allowed to import Firestore client types (docs/01-CLAUDE.md rule 6).
"""

from typing import Protocol


class Repository[T](Protocol):
    """CRUD for one school-scoped catalog/config collection — Teacher,
    Class, Subject, Room, SchoolDay, TimePeriod, LessonRequirement all
    share this exact shape (docs/05-DATABASE.md #3: each is a subcollection
    of `schools/{schoolId}`)."""

    def get(self, school_id: str, entity_id: str) -> T | None: ...

    def list(self, school_id: str) -> list[T]: ...

    def save(self, school_id: str, entity: T) -> None:
        """Upsert: creates the entity if its id is new, replaces it
        otherwise. Entities are immutable value objects on the Python
        side (docs/07-CODE_STANDARDS.md #7) — "updating" means
        `dataclasses.replace(entity, field=new_value)` then `save()`
        the result."""
        ...

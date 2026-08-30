"""Generic CRUD router factory (docs/03-ARCHITECTURE.md #26): the seven
school-scoped catalog/config entities (Teacher, Class, Subject, Room,
SchoolDay, TimePeriod, LessonRequirement) all expose the exact same
list/get/upsert shape — mirroring `app.application.repositories.generic`'s
`Repository[T]` on the persistence side — so this is written once instead
of seven times (docs/07-CODE_STANDARDS.md #1).

Route handlers here do no business logic beyond validation and a single
repository call (docs/01-CLAUDE.md rule 4): map request -> domain entity,
save, map back to a response. `PUT /{id}` is a deliberate single upsert
endpoint (create-if-absent, replace-if-present) rather than separate
POST/PATCH — entities don't have server-generated ids, so "create" and
"update" are the same operation (master prompt: "do not create endpoints
that have no real purpose").
"""

from collections.abc import Callable

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import get_current_user, require_admin
from app.application.repositories.generic import Repository
from app.core.errors import NotFoundError
from app.domain.models import User


def build_crud_router[TEntity, TResponse: BaseModel, TUpsert: BaseModel](
    *,
    prefix: str,
    tag: str,
    entity_name: str,
    repository_dependency: Callable[[], Repository[TEntity]],
    response_model: type[TResponse],
    upsert_model: type[TUpsert],
    to_response: Callable[[TEntity], TResponse],
    from_upsert: Callable[[str, str, TUpsert], TEntity],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=list[response_model])
    def list_entities(
        school_id: str = Query(...),
        _user: User = Depends(get_current_user),
        repository: Repository[TEntity] = Depends(repository_dependency),
    ) -> list[TResponse]:
        return [to_response(entity) for entity in repository.list(school_id)]

    @router.get("/{entity_id}", response_model=response_model)
    def get_entity(
        entity_id: str,
        school_id: str = Query(...),
        _user: User = Depends(get_current_user),
        repository: Repository[TEntity] = Depends(repository_dependency),
    ) -> TResponse:
        entity = repository.get(school_id, entity_id)
        if entity is None:
            raise NotFoundError(f"{entity_name} {entity_id} not found")
        return to_response(entity)

    def upsert_entity(
        entity_id: str,
        body: TUpsert,
        school_id: str = Query(...),
        _user: User = Depends(require_admin),
        repository: Repository[TEntity] = Depends(repository_dependency),
    ) -> TResponse:
        entity = from_upsert(school_id, entity_id, body)
        repository.save(school_id, entity)
        return to_response(entity)

    # `body: TUpsert` above satisfies the static checker (TUpsert is a real
    # TypeVar in scope); FastAPI itself needs the CONCRETE pydantic model to
    # build request validation, which a TypeVar can't provide, so the actual
    # runtime annotation is patched in before registering the route — the
    # standard trick generic FastAPI router factories use (e.g.
    # fastapi-utils' InferringRouter), since `typing.get_type_hints` reads
    # `__annotations__` fresh when FastAPI inspects the route, not at
    # function-definition time.
    upsert_entity.__annotations__["body"] = upsert_model
    router.add_api_route(
        "/{entity_id}", upsert_entity, methods=["PUT"], response_model=response_model
    )

    return router

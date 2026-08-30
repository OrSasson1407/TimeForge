"""`/constraints` — soft-constraint weights and solver/annealing
parameters (docs/05-DATABASE.md #19). Admin-only to write; hard
constraints are code, never persisted (docs/01-CLAUDE.md rule 8)."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_scheduling_config_repository, require_admin
from app.api.schemas.scheduling_config import (
    SchedulingConfigResponse,
    SchedulingConfigUpdateRequest,
    scheduling_config_from_update,
    scheduling_config_to_response,
)
from app.application.repositories import SchedulingConfigRepository
from app.domain.models import User

router = APIRouter(prefix="/constraints", tags=["constraints"])


@router.get("", response_model=SchedulingConfigResponse)
def get_scheduling_config(
    school_id: str = Query(...),
    _user: User = Depends(get_current_user),
    repository: SchedulingConfigRepository = Depends(get_scheduling_config_repository),
) -> SchedulingConfigResponse:
    return scheduling_config_to_response(repository.get(school_id))


@router.put("", response_model=SchedulingConfigResponse)
def update_scheduling_config(
    body: SchedulingConfigUpdateRequest,
    school_id: str = Query(...),
    _user: User = Depends(require_admin),
    repository: SchedulingConfigRepository = Depends(get_scheduling_config_repository),
) -> SchedulingConfigResponse:
    config = scheduling_config_from_update(body)
    repository.save(school_id, config)
    return scheduling_config_to_response(config)

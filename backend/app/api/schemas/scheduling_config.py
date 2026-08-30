from pydantic import BaseModel, Field

from app.domain.scheduling import SchedulingConfig


class SchedulingConfigResponse(BaseModel):
    timeout_seconds: float
    random_seed: int
    soft_constraint_weights: dict[str, float]
    initial_temperature: float
    cooling_rate: float
    min_temperature: float
    quality_decay_k: float


class SchedulingConfigUpdateRequest(BaseModel):
    timeout_seconds: float = Field(gt=0)
    random_seed: int
    soft_constraint_weights: dict[str, float]
    initial_temperature: float = Field(gt=0)
    cooling_rate: float = Field(gt=0, lt=1)
    min_temperature: float = Field(gt=0)
    quality_decay_k: float = Field(gt=0)


def scheduling_config_to_response(config: SchedulingConfig) -> SchedulingConfigResponse:
    return SchedulingConfigResponse(
        timeout_seconds=config.timeout_seconds,
        random_seed=config.random_seed,
        soft_constraint_weights=dict(config.soft_constraint_weights),
        initial_temperature=config.initial_temperature,
        cooling_rate=config.cooling_rate,
        min_temperature=config.min_temperature,
        quality_decay_k=config.quality_decay_k,
    )


def scheduling_config_from_update(body: SchedulingConfigUpdateRequest) -> SchedulingConfig:
    return SchedulingConfig(
        timeout_seconds=body.timeout_seconds,
        random_seed=body.random_seed,
        soft_constraint_weights=dict(body.soft_constraint_weights),
        initial_temperature=body.initial_temperature,
        cooling_rate=body.cooling_rate,
        min_temperature=body.min_temperature,
        quality_decay_k=body.quality_decay_k,
    )

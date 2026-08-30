/** Mirrors backend/app/api/schemas/scheduling_config.py. */
export interface SchedulingConfig {
  timeout_seconds: number
  random_seed: number
  soft_constraint_weights: Record<string, number>
  initial_temperature: number
  cooling_rate: number
  min_temperature: number
  quality_decay_k: number
}

export type SchedulingConfigUpdateRequest = SchedulingConfig

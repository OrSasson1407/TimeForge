/**
 * Teacher/class availability records.
 *
 * Aliases over the generated OpenAPI schema — see `catalog.ts` for why.
 */
import type { components } from './api.generated'

type Schemas = components['schemas']

/** One (owner, day, period) availability record. `day_id` may be null: a
 * null day means the record applies to that period on every day, which the
 * grid renders but does not itself create. */
export type Availability = Schemas['AvailabilityResponse']

export type AvailabilityUpsertRequest = Schemas['AvailabilityUpsertRequest']

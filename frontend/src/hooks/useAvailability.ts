import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { availabilityApi } from '../services/availabilityApi'
import type { OwnerType } from '../types/enums'
import type { Availability, AvailabilityUpsertRequest } from '../types/availability'

export function useAvailabilityForOwner(
  schoolId: string | undefined,
  ownerType: OwnerType | undefined,
  ownerId: string | undefined,
) {
  return useQuery({
    queryKey: ['availability', schoolId, ownerType, ownerId],
    queryFn: () => availabilityApi.listForOwner(schoolId!, ownerType!, ownerId!),
    enabled: !!schoolId && !!ownerType && !!ownerId,
  })
}

export function useAllAvailability(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['availability', schoolId, 'all'],
    queryFn: () => availabilityApi.listAll(schoolId!),
    enabled: !!schoolId,
  })
}

/** Optimistic: a click flips the grid cell immediately rather than waiting
 * on a round-trip — safe here specifically because this is a plain
 * idempotent upsert-by-deterministic-id with no server-side validation or
 * version concurrency to get wrong (unlike a schedule move, which always
 * waits for a real server verdict). A failure rolls the cell back and
 * surfaces the real error via the global mutation-error toast. */
export function useUpsertAvailability(schoolId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AvailabilityUpsertRequest }) =>
      availabilityApi.upsert(schoolId!, id, body),
    onMutate: async ({ id, body }) => {
      const queryKey = ['availability', schoolId, body.owner_type, body.owner_id]
      await queryClient.cancelQueries({ queryKey })
      const previous = queryClient.getQueryData<Availability[]>(queryKey)

      queryClient.setQueryData<Availability[]>(queryKey, (old) => {
        const optimisticRecord: Availability = { id, school_id: schoolId!, ...body }
        const existingIndex = (old ?? []).findIndex(
          (r) => r.day_id === body.day_id && r.time_period_id === body.time_period_id,
        )
        if (!old || existingIndex === -1) return [...(old ?? []), optimisticRecord]
        const next = [...old]
        next[existingIndex] = optimisticRecord
        return next
      })

      return { previous, queryKey }
    },
    onError: (_err, _variables, context) => {
      if (context) queryClient.setQueryData(context.queryKey, context.previous)
    },
    onSettled: (_data, _err, { body }) => {
      void queryClient.invalidateQueries({
        queryKey: ['availability', schoolId, body.owner_type, body.owner_id],
      })
    },
  })
}

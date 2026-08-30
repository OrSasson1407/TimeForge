import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { availabilityApi } from '../services/availabilityApi'
import type { OwnerType } from '../types/enums'
import type { AvailabilityUpsertRequest } from '../types/availability'

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

export function useUpsertAvailability(schoolId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AvailabilityUpsertRequest }) =>
      availabilityApi.upsert(schoolId!, id, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['availability', schoolId] })
    },
  })
}

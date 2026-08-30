import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { schedulingConfigApi } from '../services/schedulingConfigApi'
import type { SchedulingConfigUpdateRequest } from '../types/schedulingConfig'

export function useSchedulingConfig(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['scheduling-config', schoolId],
    queryFn: () => schedulingConfigApi.get(schoolId!),
    enabled: !!schoolId,
  })
}

export function useUpdateSchedulingConfig(schoolId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SchedulingConfigUpdateRequest) =>
      schedulingConfigApi.update(schoolId!, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['scheduling-config', schoolId] })
    },
  })
}

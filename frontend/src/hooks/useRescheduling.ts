import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reschedulingApi } from '../services/reschedulingApi'
import type { ReportDisruptionRequest } from '../types/rescheduling'

export function useReschedulingEvents(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['rescheduling-events', schoolId],
    queryFn: () => reschedulingApi.listEvents(schoolId!),
    enabled: !!schoolId,
  })
}

export function useReportDisruption(schoolId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ReportDisruptionRequest) => reschedulingApi.reschedule(schoolId!, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['rescheduling-events', schoolId] })
      void queryClient.invalidateQueries({ queryKey: ['schedule-versions', schoolId] })
      void queryClient.invalidateQueries({ queryKey: ['schedule', schoolId] })
    },
  })
}

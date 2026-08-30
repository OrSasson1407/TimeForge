import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { scheduleApi } from '../services/scheduleApi'
import type {
  ApplyMoveRequest,
  GenerateScheduleRequest,
  ProposedMove,
  PublishRequest,
} from '../types/schedule'

export function useSchedule(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['schedule', schoolId],
    queryFn: () => scheduleApi.get(schoolId!),
    enabled: !!schoolId,
  })
}

export function useScheduleVersions(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['schedule-versions', schoolId],
    queryFn: () => scheduleApi.listVersions(schoolId!),
    enabled: !!schoolId,
  })
}

export function useScheduleVersion(schoolId: string | undefined, versionId: string | undefined) {
  return useQuery({
    queryKey: ['schedule-version', schoolId, versionId],
    queryFn: () => scheduleApi.getVersion(schoolId!, versionId!),
    enabled: !!schoolId && !!versionId,
  })
}

export function useScheduleAssignments(
  schoolId: string | undefined,
  versionId: string | undefined,
) {
  return useQuery({
    queryKey: ['schedule-assignments', schoolId, versionId],
    queryFn: () => scheduleApi.listAssignments(schoolId!, versionId!),
    enabled: !!schoolId && !!versionId,
  })
}

export function useCompareVersions(
  schoolId: string | undefined,
  fromVersionId: string | undefined,
  toVersionId: string | undefined,
) {
  return useQuery({
    queryKey: ['schedule-compare', schoolId, fromVersionId, toVersionId],
    queryFn: () => scheduleApi.compare(schoolId!, fromVersionId!, toVersionId!),
    enabled: !!schoolId && !!fromVersionId && !!toVersionId,
  })
}

function useInvalidateScheduleQueries(schoolId: string | undefined) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: ['schedule', schoolId] })
    void queryClient.invalidateQueries({ queryKey: ['schedule-versions', schoolId] })
  }
}

export function useGenerateSchedule(schoolId: string | undefined) {
  const invalidate = useInvalidateScheduleQueries(schoolId)
  return useMutation({
    mutationFn: (body: GenerateScheduleRequest) => scheduleApi.generate(schoolId!, body),
    onSuccess: invalidate,
  })
}

export function useValidateMove(schoolId: string | undefined, versionId: string | undefined) {
  return useMutation({
    mutationFn: (move: ProposedMove) => scheduleApi.validateMove(schoolId!, versionId!, move),
  })
}

export function useApplyMove(schoolId: string | undefined, versionId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ApplyMoveRequest) => scheduleApi.applyMove(schoolId!, versionId!, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule-assignments', schoolId, versionId],
      })
      void queryClient.invalidateQueries({ queryKey: ['schedule-version', schoolId, versionId] })
      void queryClient.invalidateQueries({ queryKey: ['schedule-versions', schoolId] })
    },
  })
}

export function usePublishVersion(schoolId: string | undefined, versionId: string | undefined) {
  const invalidate = useInvalidateScheduleQueries(schoolId)
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: PublishRequest) => scheduleApi.publish(schoolId!, versionId!, body),
    onSuccess: () => {
      invalidate()
      void queryClient.invalidateQueries({ queryKey: ['schedule-version', schoolId, versionId] })
    },
  })
}

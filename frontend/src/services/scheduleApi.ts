import { apiClient } from './apiClient'
import type {
  ApplyMoveRequest,
  CompareVersionsResponse,
  GenerateScheduleRequest,
  GenerateScheduleResponse,
  ProposedMove,
  PublishRequest,
  Schedule,
  ScheduleAssignment,
  ScheduleVersion,
  ValidateMoveResponse,
} from '../types/schedule'

export const scheduleApi = {
  get: (schoolId: string) => apiClient.get<Schedule>(`/schedules?school_id=${schoolId}`),

  generate: (schoolId: string, body: GenerateScheduleRequest) =>
    apiClient.post<GenerateScheduleResponse>(`/schedules/generate?school_id=${schoolId}`, body),

  listVersions: (schoolId: string) =>
    apiClient.get<ScheduleVersion[]>(`/schedules/versions?school_id=${schoolId}`),

  getVersion: (schoolId: string, versionId: string) =>
    apiClient.get<ScheduleVersion>(`/schedules/versions/${versionId}?school_id=${schoolId}`),

  listAssignments: (schoolId: string, versionId: string) =>
    apiClient.get<ScheduleAssignment[]>(
      `/schedules/versions/${versionId}/assignments?school_id=${schoolId}`,
    ),

  validateMove: (schoolId: string, versionId: string, move: ProposedMove) =>
    apiClient.post<ValidateMoveResponse>(
      `/schedules/versions/${versionId}/validate-move?school_id=${schoolId}`,
      move,
    ),

  applyMove: (schoolId: string, versionId: string, body: ApplyMoveRequest) =>
    apiClient.post<ScheduleAssignment>(
      `/schedules/versions/${versionId}/apply-move?school_id=${schoolId}`,
      body,
    ),

  publish: (schoolId: string, versionId: string, body: PublishRequest) =>
    apiClient.post<ScheduleVersion>(
      `/schedules/versions/${versionId}/publish?school_id=${schoolId}`,
      body,
    ),

  compare: (schoolId: string, fromVersionId: string, toVersionId: string) =>
    apiClient.get<CompareVersionsResponse>(
      `/schedules/compare?school_id=${schoolId}&from_version_id=${fromVersionId}&to_version_id=${toVersionId}`,
    ),
}

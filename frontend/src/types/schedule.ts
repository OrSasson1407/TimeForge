/**
 * The scheduling workflow: versions, assignments, moves, analytics.
 *
 * Aliases over the generated OpenAPI schema — see `catalog.ts` for why.
 * Note `ValidateMoveResponse['result']`: it is a real union here only
 * because the backend declares it as a `Literal`. When it was a bare `str`
 * this file carried a hand-written union that the contract did not actually
 * guarantee.
 */
import type { components } from './api.generated'

type Schemas = components['schemas']

export type Schedule = Schemas['ScheduleResponse']
export type ScheduleScore = Schemas['ScheduleScoreResponse']
export type ScheduleVersion = Schemas['ScheduleVersionResponse']
export type ScheduleAssignment = Schemas['ScheduleAssignmentResponse']

export type GenerateScheduleRequest = Schemas['GenerateScheduleRequest']
export type GenerateScheduleResponse = Schemas['GenerateScheduleResponse']
export type BottleneckReport = Schemas['BottleneckResponse']
export type InfeasibilityReport = Schemas['InfeasibilityResponse']
export type SearchStats = Schemas['SearchStatsResponse']

export type ProposedMove = Schemas['ProposedMove']
export type ApplyMoveRequest = Schemas['ApplyMoveRequest']
export type ValidateMoveResponse = Schemas['ValidateMoveResponse']
export type Violation = Schemas['ViolationResponse']
export type PublishRequest = Schemas['PublishRequest']

export type TeacherWorkload = Schemas['TeacherWorkloadResponse']
export type RoomUtilization = Schemas['RoomUtilizationResponse']
export type ClassCoverage = Schemas['ClassCoverageResponse']
export type ScheduleAnalytics = Schemas['ScheduleAnalyticsResponse']

export type AssignmentDiffEntry = Schemas['AssignmentDiffEntry']
export type CompareVersionsResponse = Schemas['CompareVersionsResponse']

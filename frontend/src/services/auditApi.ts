import { apiClient } from './apiClient'
import type { AuditEntityType } from '../types/enums'
import type { AuditEvent } from '../types/audit'

export const auditApi = {
  listForEntity: (entityType: AuditEntityType, entityId: string) =>
    apiClient.get<AuditEvent[]>(`/audit?entity_type=${entityType}&entity_id=${entityId}`),
  listForActor: (actorUserId: string) =>
    apiClient.get<AuditEvent[]>(`/audit?actor_user_id=${actorUserId}`),
}

import { useQuery } from '@tanstack/react-query'
import { auditApi } from '../services/auditApi'
import type { AuditEntityType } from '../types/enums'

export function useAuditForEntity(
  entityType: AuditEntityType | undefined,
  entityId: string | undefined,
) {
  return useQuery({
    queryKey: ['audit', entityType, entityId],
    queryFn: () => auditApi.listForEntity(entityType!, entityId!),
    enabled: !!entityType && !!entityId,
  })
}

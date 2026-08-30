import type { AuditEntityType, AuditOperation, UserRole } from './enums'

/** Mirrors backend/app/api/schemas/audit.py. */
export interface Actor {
  user_id: string
  role: UserRole
}

export interface AuditEvent {
  id: string
  actor: Actor
  timestamp: string
  operation: AuditOperation
  entity_type: AuditEntityType
  entity_id: string
  before: Record<string, unknown> | null
  after: Record<string, unknown> | null
  reason: string | null
}

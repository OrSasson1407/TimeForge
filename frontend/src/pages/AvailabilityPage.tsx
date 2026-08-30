import { useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { schoolDayHooks, timePeriodHooks, teacherHooks, classHooks } from '../hooks/useCatalog'
import { useAvailabilityForOwner } from '../hooks/useAvailability'
import { AvailabilityGrid } from '../features/availability/AvailabilityGrid'
import type { OwnerType } from '../types/enums'

export function AvailabilityPage() {
  const { user } = useAuth()
  const schoolId = user?.school_id
  const isAdmin = user?.role === 'ADMIN'

  const [ownerType, setOwnerType] = useState<OwnerType>('TEACHER')
  const [ownerId, setOwnerId] = useState<string>(user?.teacher_id ?? '')

  const { data: days } = schoolDayHooks.useList(schoolId)
  const { data: periods } = timePeriodHooks.useList(schoolId)
  const { data: teachers } = teacherHooks.useList(isAdmin ? schoolId : undefined)
  const { data: classes } = classHooks.useList(isAdmin ? schoolId : undefined)
  const effectiveOwnerId = isAdmin ? ownerId : (user?.teacher_id ?? '')
  const { data: records } = useAvailabilityForOwner(
    schoolId,
    ownerType,
    effectiveOwnerId || undefined,
  )

  if (!isAdmin && !user?.teacher_id) {
    return <p>Your account has no linked teacher record, so there is no availability to submit.</p>
  }

  return (
    <main>
      <h2>Availability</h2>

      {isAdmin && (
        <div>
          <label htmlFor="availability-owner-type">Owner type</label>
          <select
            id="availability-owner-type"
            value={ownerType}
            onChange={(e) => {
              setOwnerType(e.target.value as OwnerType)
              setOwnerId('')
            }}
          >
            <option value="TEACHER">Teacher</option>
            <option value="CLASS">Class</option>
          </select>

          <label htmlFor="availability-owner-id">
            {ownerType === 'TEACHER' ? 'Teacher' : 'Class'}
          </label>
          <select
            id="availability-owner-id"
            value={ownerId}
            onChange={(e) => setOwnerId(e.target.value)}
          >
            <option value="">Select…</option>
            {(ownerType === 'TEACHER' ? teachers : classes)?.map((entity) => (
              <option key={entity.id} value={entity.id}>
                {entity.id} — {entity.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {days && periods && effectiveOwnerId ? (
        <AvailabilityGrid
          schoolId={schoolId!}
          ownerType={ownerType}
          ownerId={effectiveOwnerId}
          days={days}
          periods={periods}
          records={records ?? []}
        />
      ) : (
        <p>{effectiveOwnerId ? 'Loading…' : 'Select an owner to view their availability.'}</p>
      )}
    </main>
  )
}

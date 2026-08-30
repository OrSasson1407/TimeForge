import { useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useLanguage } from '../state/LanguageContext'
import { schoolDayHooks, timePeriodHooks, teacherHooks, classHooks } from '../hooks/useCatalog'
import { useAvailabilityForOwner } from '../hooks/useAvailability'
import { AvailabilityGrid } from '../features/availability/AvailabilityGrid'
import type { OwnerType } from '../types/enums'

export function AvailabilityPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
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
    return <p>{t('availability.noTeacherRecord')}</p>
  }

  return (
    <main>
      <h2>{t('availability.title')}</h2>

      {isAdmin && (
        <div>
          <label htmlFor="availability-owner-type">{t('availability.ownerType')}</label>
          <select
            id="availability-owner-type"
            value={ownerType}
            onChange={(e) => {
              setOwnerType(e.target.value as OwnerType)
              setOwnerId('')
            }}
          >
            <option value="TEACHER">{t('availability.teacher')}</option>
            <option value="CLASS">{t('availability.class')}</option>
          </select>

          <label htmlFor="availability-owner-id">
            {ownerType === 'TEACHER' ? t('availability.teacher') : t('availability.class')}
          </label>
          <select
            id="availability-owner-id"
            value={ownerId}
            onChange={(e) => setOwnerId(e.target.value)}
          >
            <option value="">{t('availability.select')}</option>
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
        <p>{effectiveOwnerId ? t('availability.loading') : t('availability.selectOwner')}</p>
      )}
    </main>
  )
}

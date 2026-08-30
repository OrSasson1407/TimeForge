import { useQuery } from '@tanstack/react-query'
import { schoolApi } from '../services/schoolApi'

export function useSchool(schoolId: string | undefined) {
  return useQuery({
    queryKey: ['school', schoolId],
    queryFn: () => schoolApi.get(schoolId!),
    enabled: !!schoolId,
  })
}

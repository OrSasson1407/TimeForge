/**
 * Generic react-query hook pair for a `CrudApi<TEntity, TUpsert>`
 * (services/crudApi.ts) — the frontend half of the same DRY choice the
 * backend makes with `build_crud_router`: one implementation of "list +
 * upsert, cache-invalidate on write" shared by all seven catalog entities,
 * not seven copies (docs/07-CODE_STANDARDS.md #9: fetched data flows
 * through a small dedicated data-fetching layer, not ad hoc `useState`).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { CrudApi } from '../services/crudApi'

export function createCrudHooks<TEntity, TUpsert>(
  resourceKey: string,
  api: CrudApi<TEntity, TUpsert>,
) {
  function useList(schoolId: string | undefined) {
    return useQuery({
      queryKey: [resourceKey, schoolId, 'list'],
      queryFn: () => api.list(schoolId!),
      enabled: !!schoolId,
    })
  }

  function useUpsert(schoolId: string | undefined) {
    const queryClient = useQueryClient()
    return useMutation({
      mutationFn: ({ id, body }: { id: string; body: TUpsert }) => api.upsert(schoolId!, id, body),
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: [resourceKey, schoolId, 'list'] })
      },
    })
  }

  return { useList, useUpsert }
}

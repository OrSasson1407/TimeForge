/**
 * Generic school-scoped CRUD client, mirroring the backend's generic
 * `build_crud_router` factory (backend/app/api/crud_router.py) — the same
 * list/get/upsert shape, built once and reused for the seven catalog
 * entities, rather than seven near-identical hand-written clients.
 */
import { apiClient } from './apiClient'

export interface CrudApi<TEntity, TUpsert> {
  list: (schoolId: string) => Promise<TEntity[]>
  get: (schoolId: string, id: string) => Promise<TEntity>
  upsert: (schoolId: string, id: string, body: TUpsert) => Promise<TEntity>
}

export function createCrudApi<TEntity, TUpsert>(basePath: string): CrudApi<TEntity, TUpsert> {
  return {
    list: (schoolId) => apiClient.get<TEntity[]>(`${basePath}?school_id=${schoolId}`),
    get: (schoolId, id) => apiClient.get<TEntity>(`${basePath}/${id}?school_id=${schoolId}`),
    upsert: (schoolId, id, body) =>
      apiClient.put<TEntity>(`${basePath}/${id}?school_id=${schoolId}`, body),
  }
}

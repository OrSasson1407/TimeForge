/**
 * Identity, registration and the admin approval flow.
 *
 * Aliases over the generated OpenAPI schema — see `catalog.ts` for why the
 * frontend no longer keeps its own copy of these shapes.
 */
import type { components } from './api.generated'

type Schemas = components['schemas']

/** The backend's own record of the signed-in user: role, school and the
 * linked teacher id. The role here is authoritative — it is never taken
 * from the Firebase identity. */
export type User = Schemas['UserResponse']

/** The unauthenticated school picker on the registration page. */
export type PublicSchool = Schemas['PublicSchoolResponse']

export type RegisterRequest = Schemas['RegisterRequest']
export type RegisterResponse = Schemas['RegisterResponse']

export type PendingUser = Schemas['PendingUserResponse']
export type ApproveUserRequest = Schemas['ApproveUserRequest']

/** The admin-facing "all users" list — unlike `User`, it carries the email
 * address, because an admin managing accounts needs to tell them apart. */
export type AdminUser = Schemas['AdminUserResponse']

export type CompleteOAuthProfileRequest = Schemas['CompleteOAuthProfileRequest']

import type { UserRole } from './enums'

/** Mirrors backend/app/api/schemas/auth.py's UserResponse. */
export interface User {
  id: string
  role: UserRole
  school_id: string
  display_name: string
  teacher_id: string | null
  email_verified: boolean
  is_active: boolean
  created_at: string
}

/** Mirrors backend/app/api/schemas/school.py's PublicSchoolResponse — the
 * unauthenticated school picker shown on the registration page. */
export interface PublicSchool {
  id: string
  name: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
  school_id: string
  recaptcha_token: string
}

export interface RegisterResponse {
  user_id: string
  email: string
  message: string
}

export interface PendingUser {
  id: string
  email: string
  display_name: string
  school_id: string
  created_at: string
}

export interface ApproveUserRequest {
  role: 'ADMIN' | 'TEACHER'
  teacher_id: string | null
}

/** Mirrors backend/app/api/schemas/auth.py's AdminUserResponse — the
 * "all users" list used for suspend/reactivate, distinct from the
 * pending-approval queue. */
export interface AdminUser {
  id: string
  email: string
  role: UserRole
  school_id: string
  display_name: string
  teacher_id: string | null
  is_active: boolean
  created_at: string
}

export interface CompleteOAuthProfileRequest {
  display_name: string
  school_id: string
}

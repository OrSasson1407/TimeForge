import { apiClient } from './apiClient'
import type {
  AdminUser,
  ApproveUserRequest,
  CompleteOAuthProfileRequest,
  PendingUser,
  PublicSchool,
  RegisterRequest,
  RegisterResponse,
  User,
} from '../types/auth'

interface MessageResponse {
  message: string
}

export const authApi = {
  me: () => apiClient.get<User>('/auth/me'),
  register: (body: RegisterRequest) => apiClient.post<RegisterResponse>('/auth/register', body),
  completeOAuthProfile: (body: CompleteOAuthProfileRequest) =>
    apiClient.post<RegisterResponse>('/auth/complete-oauth-profile', body),
  verifyCode: (email: string, code: string) =>
    apiClient.post<MessageResponse>('/auth/verify-code', { email, code }),
  resendCode: (email: string) => apiClient.post<MessageResponse>('/auth/resend-code', { email }),
  publicSchools: () => apiClient.get<PublicSchool[]>('/public/schools'),
  pendingUsers: () => apiClient.get<PendingUser[]>('/users/pending'),
  approveUser: (userId: string, body: ApproveUserRequest) =>
    apiClient.post<User>(`/users/${userId}/approve`, body),
  rejectUser: (userId: string) => apiClient.post<MessageResponse>(`/users/${userId}/reject`),
  listUsers: () => apiClient.get<AdminUser[]>('/users'),
  suspendUser: (userId: string) => apiClient.post<User>(`/users/${userId}/suspend`),
  reactivateUser: (userId: string) => apiClient.post<User>(`/users/${userId}/reactivate`),
  revokeSessions: () => apiClient.post<MessageResponse>('/auth/security/revoke-sessions'),
}

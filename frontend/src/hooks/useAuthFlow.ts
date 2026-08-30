/**
 * Data-fetching hooks for the registration/approval flow (mirrors
 * useCrud.ts's "fetched data flows through a small dedicated layer, not ad
 * hoc useState", docs/07-CODE_STANDARDS.md #9).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../services/authApi'
import type {
  ApproveUserRequest,
  CompleteOAuthProfileRequest,
  RegisterRequest,
} from '../types/auth'

export function usePublicSchools() {
  return useQuery({
    queryKey: ['public-schools'],
    queryFn: () => authApi.publicSchools(),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (body: RegisterRequest) => authApi.register(body),
  })
}

export function useVerifyCode() {
  return useMutation({
    mutationFn: ({ email, code }: { email: string; code: string }) =>
      authApi.verifyCode(email, code),
  })
}

export function useResendCode() {
  return useMutation({
    mutationFn: (email: string) => authApi.resendCode(email),
  })
}

export function usePendingUsers(enabled: boolean) {
  return useQuery({
    queryKey: ['pending-users'],
    queryFn: () => authApi.pendingUsers(),
    enabled,
  })
}

export function useApproveUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, body }: { userId: string; body: ApproveUserRequest }) =>
      authApi.approveUser(userId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['pending-users'] })
    },
  })
}

export function useRejectUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => authApi.rejectUser(userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['pending-users'] })
    },
  })
}

export function useCompleteOAuthProfile() {
  return useMutation({
    mutationFn: (body: CompleteOAuthProfileRequest) => authApi.completeOAuthProfile(body),
  })
}

export function useUsers(enabled: boolean) {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => authApi.listUsers(),
    enabled,
  })
}

export function useSuspendUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => authApi.suspendUser(userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useReactivateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => authApi.reactivateUser(userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

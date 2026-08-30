import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { queryClient } from './queryClient'
import { AuthProvider } from '../state/AuthContext'
import { AppHeader } from '../components/AppHeader'
import { RequireAdmin, RequireAuth } from '../components/RequireAuth'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage'
import { CompleteProfilePage } from '../pages/CompleteProfilePage'
import { VerifyCodePage } from '../pages/VerifyCodePage'
import { PendingApprovalPage } from '../pages/PendingApprovalPage'
import { AdminPendingApprovalsPage } from '../pages/AdminPendingApprovalsPage'
import { AdminUsersPage } from '../pages/AdminUsersPage'
import { DashboardPage } from '../pages/DashboardPage'
import { ManagementPage } from '../pages/ManagementPage'
import { AvailabilityPage } from '../pages/AvailabilityPage'
import { ConstraintsPage } from '../pages/ConstraintsPage'
import { SchedulePage } from '../pages/SchedulePage'
import { AuditPage } from '../pages/AuditPage'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppHeader />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/verify-email" element={<VerifyCodePage />} />
            <Route path="/complete-profile" element={<CompleteProfilePage />} />
            <Route path="/pending-approval" element={<PendingApprovalPage />} />
            <Route element={<RequireAuth />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/availability" element={<AvailabilityPage />} />
              <Route element={<RequireAdmin />}>
                <Route path="/management" element={<ManagementPage />} />
                <Route path="/constraints" element={<ConstraintsPage />} />
                <Route path="/audit" element={<AuditPage />} />
                <Route path="/pending-approvals" element={<AdminPendingApprovalsPage />} />
                <Route path="/users" element={<AdminUsersPage />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

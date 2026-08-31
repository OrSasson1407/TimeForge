import { useEffect, useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { queryClient } from './queryClient'
import { AuthProvider } from '../state/AuthContext'
import { ThemeProvider } from '../state/ThemeContext'
import { LanguageProvider, useLanguage } from '../state/LanguageContext'
import { AppHeader } from '../components/AppHeader'
import { RequireAdmin, RequireAuth } from '../components/RequireAuth'
import { ToastContainer } from '../components/ToastContainer'
import { OfflineBanner } from '../components/OfflineBanner'
import { KeyboardShortcutsHelp } from '../components/KeyboardShortcutsHelp'
import { CommandPalette } from '../components/CommandPalette'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
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
import { AnalyticsPage } from '../pages/AnalyticsPage'
import { SecurityPage } from '../pages/SecurityPage'

function AppShell() {
  const { t } = useLanguage()
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [showPalette, setShowPalette] = useState(false)
  useKeyboardShortcuts(() => setShowShortcuts(true))

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setShowPalette(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <>
      <a href="#main-content" className="skip-link">
        {t('common.skipToContent')}
      </a>
      <OfflineBanner />
      <AppHeader />
      {/* A plain div, not <main> — every page below already renders its own
          <main> landmark; this is only a focus anchor for the skip link. */}
      <div id="main-content" tabIndex={-1}>
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
            <Route path="/security" element={<SecurityPage />} />
            <Route element={<RequireAdmin />}>
              <Route path="/management" element={<ManagementPage />} />
              <Route path="/constraints" element={<ConstraintsPage />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/pending-approvals" element={<AdminPendingApprovalsPage />} />
              <Route path="/users" element={<AdminUsersPage />} />
            </Route>
          </Route>
        </Routes>
      </div>
      <ToastContainer />
      {showShortcuts && <KeyboardShortcutsHelp onClose={() => setShowShortcuts(false)} />}
      {showPalette && <CommandPalette onClose={() => setShowPalette(false)} />}
    </>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          <BrowserRouter>
            <AuthProvider>
              <AppShell />
            </AuthProvider>
          </BrowserRouter>
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { MainLayout } from '@/components/layout/MainLayout'
import { Dashboard } from '@/pages/Dashboard'
import { LiveOdds } from '@/pages/LiveOdds'
import { Analysis } from '@/pages/Analysis'
import { Alerts } from '@/pages/Alerts'
import { Portfolio } from '@/pages/Portfolio'
import { Settings } from '@/pages/Settings'
import { Login } from '@/pages/Login'
import { PlayerProps } from '@/pages/PlayerProps'
import { SocialTrading } from '@/pages/SocialTrading'
import { Strategies } from '@/pages/Strategies'
import { Toaster } from 'react-hot-toast'
import type { ReactNode } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1F2937',
              color: '#F3F4F6',
              border: '1px solid #374151',
            },
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="odds" element={<LiveOdds />} />
            <Route path="analysis" element={<Analysis />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="portfolio" element={<Portfolio />} />
            <Route path="player-props" element={<PlayerProps />} />
            <Route path="social" element={<SocialTrading />} />
            <Route path="strategies" element={<Strategies />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
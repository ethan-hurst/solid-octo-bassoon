import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/api/client'
import { User, AuthResponse } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        // Mock auth for now since backend lacks auth endpoints
        if (import.meta.env.VITE_ENABLE_MOCK_AUTH === 'true') {
          const mockUser: User = {
            id: '1',
            email,
            username: email.split('@')[0],
            is_active: true,
            sports: [],
            min_edge: 0.05,
            max_kelly_fraction: 0.25,
            notification_channels: ['websocket', 'email']
          }
          const mockToken = 'mock-jwt-token-' + Date.now()
          
          set({
            user: mockUser,
            token: mockToken,
            isAuthenticated: true,
          })
          localStorage.setItem('authToken', mockToken)
          return
        }
        
        // Real auth implementation
        const { data } = await apiClient.post<AuthResponse>('/auth/login', { email, password })
        set({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
        })
        localStorage.setItem('authToken', data.access_token)
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        localStorage.removeItem('authToken')
      },
      
      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)